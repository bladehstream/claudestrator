"""
EPSS Enrichment Service.

Background service that queries FIRST.org EPSS API to enrich
curated vulnerabilities with exploitation probability scores.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import httpx
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Vulnerability

logger = logging.getLogger(__name__)

# FIRST.org EPSS API configuration
EPSS_API_BASE_URL = "https://api.first.org/data/v1/epss"
EPSS_API_TIMEOUT = 30.0
EPSS_RATE_LIMIT_DELAY = 1.0  # Delay between requests in seconds
EPSS_MAX_RETRIES = 3
EPSS_RETRY_DELAY = 5.0


class EPSSEnrichmentService:
    """
    Service for enriching vulnerabilities with EPSS scores.

    Queries FIRST.org EPSS API for exploitation probability scores
    and updates the epss_score field in curated vulnerabilities.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize EPSS enrichment service.

        Args:
            db: Database session
        """
        self.db = db
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Context manager entry."""
        self.client = httpx.AsyncClient(timeout=EPSS_API_TIMEOUT)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.client:
            await self.client.aclose()

    async def _fetch_epss_score(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch EPSS score for a single CVE from FIRST.org API.

        Args:
            cve_id: CVE identifier (e.g., CVE-2024-1234)

        Returns:
            Dictionary with epss and percentile, or None if not found
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use context manager.")

        url = f"{EPSS_API_BASE_URL}?cve={cve_id}"

        for attempt in range(1, EPSS_MAX_RETRIES + 1):
            try:
                logger.debug(f"Fetching EPSS for {cve_id} (attempt {attempt}/{EPSS_MAX_RETRIES})")

                response = await self.client.get(url)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", EPSS_RETRY_DELAY * attempt))
                    logger.warning(f"Rate limited by EPSS API. Retrying after {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue

                # Handle not found (CVE not in EPSS database)
                if response.status_code == 404:
                    logger.debug(f"CVE {cve_id} not found in EPSS database (404)")
                    return None

                # Raise for other HTTP errors
                response.raise_for_status()

                data = response.json()

                # Parse response
                if "data" in data and len(data["data"]) > 0:
                    epss_data = data["data"][0]
                    return {
                        "epss": float(epss_data.get("epss", 0.0)),
                        "percentile": float(epss_data.get("percentile", 0.0))
                    }
                else:
                    logger.debug(f"No EPSS data found for {cve_id}")
                    return None

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching EPSS for {cve_id}: {e}")
                if attempt == EPSS_MAX_RETRIES:
                    return None
                await asyncio.sleep(EPSS_RETRY_DELAY * attempt)

            except httpx.RequestError as e:
                logger.error(f"Request error fetching EPSS for {cve_id}: {e}")
                if attempt == EPSS_MAX_RETRIES:
                    return None
                await asyncio.sleep(EPSS_RETRY_DELAY * attempt)

            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing EPSS response for {cve_id}: {e}")
                return None

        return None

    async def get_vulnerabilities_needing_enrichment(
        self,
        limit: int = 100,
        max_age_days: Optional[int] = 7
    ) -> List[Vulnerability]:
        """
        Get vulnerabilities that need EPSS enrichment.

        Selects vulnerabilities that either:
        - Have never been enriched (epss_score is NULL)
        - Were enriched more than max_age_days ago

        Args:
            limit: Maximum number of vulnerabilities to return
            max_age_days: Re-enrich if older than this many days (None = only enrich once)

        Returns:
            List of Vulnerability objects needing enrichment
        """
        # Build query for vulnerabilities needing enrichment
        conditions = []

        # Never enriched
        conditions.append(Vulnerability.epss_score.is_(None))

        # Re-enrich old scores
        if max_age_days is not None:
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            conditions.append(
                and_(
                    Vulnerability.enriched_at.isnot(None),
                    Vulnerability.enriched_at < cutoff_date
                )
            )

        query = (
            select(Vulnerability)
            .where(or_(*conditions))
            .order_by(Vulnerability.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def enrich_vulnerability(self, vulnerability: Vulnerability) -> bool:
        """
        Enrich a single vulnerability with EPSS score.

        Args:
            vulnerability: Vulnerability object to enrich

        Returns:
            True if enrichment succeeded, False otherwise
        """
        try:
            epss_data = await self._fetch_epss_score(vulnerability.cve_id)

            if epss_data:
                # Update only EPSS fields, preserving all other metadata
                vulnerability.epss_score = epss_data["epss"]
                vulnerability.epss_percentile = epss_data["percentile"]
                vulnerability.enriched_at = datetime.utcnow()

                await self.db.commit()

                logger.info(
                    f"Enriched {vulnerability.cve_id} with EPSS score: "
                    f"{epss_data['epss']:.4f} (percentile: {epss_data['percentile']:.2f})"
                )
                return True
            else:
                logger.debug(f"No EPSS data available for {vulnerability.cve_id}")
                return False

        except Exception as e:
            logger.error(f"Error enriching {vulnerability.cve_id}: {e}", exc_info=True)
            await self.db.rollback()
            return False

    async def enrich_batch(
        self,
        limit: int = 100,
        max_age_days: Optional[int] = 7,
        rate_limit_delay: float = EPSS_RATE_LIMIT_DELAY
    ) -> Dict[str, int]:
        """
        Enrich a batch of vulnerabilities with EPSS scores.

        Args:
            limit: Maximum number of vulnerabilities to enrich
            max_age_days: Re-enrich scores older than this many days
            rate_limit_delay: Delay between API requests in seconds

        Returns:
            Statistics dictionary with counts
        """
        stats = {
            "processed": 0,
            "enriched": 0,
            "not_found": 0,
            "errors": 0
        }

        # Get vulnerabilities needing enrichment
        vulnerabilities = await self.get_vulnerabilities_needing_enrichment(
            limit=limit,
            max_age_days=max_age_days
        )

        logger.info(f"Found {len(vulnerabilities)} vulnerabilities needing EPSS enrichment")

        # Process each vulnerability with rate limiting
        for vuln in vulnerabilities:
            stats["processed"] += 1

            success = await self.enrich_vulnerability(vuln)

            if success:
                stats["enriched"] += 1
            else:
                # Check if it was not found vs error
                # For now, count as not_found
                stats["not_found"] += 1

            # Rate limiting delay
            if stats["processed"] < len(vulnerabilities):
                await asyncio.sleep(rate_limit_delay)

        logger.info(
            f"EPSS enrichment complete: {stats['enriched']} enriched, "
            f"{stats['not_found']} not found, {stats['errors']} errors"
        )

        return stats


async def run_epss_enrichment(
    db: AsyncSession,
    limit: int = 100,
    max_age_days: Optional[int] = 7
) -> Dict[str, int]:
    """
    Convenience function to run EPSS enrichment.

    Args:
        db: Database session
        limit: Maximum number of vulnerabilities to enrich
        max_age_days: Re-enrich scores older than this many days

    Returns:
        Statistics dictionary
    """
    async with EPSSEnrichmentService(db) as service:
        return await service.enrich_batch(
            limit=limit,
            max_age_days=max_age_days
        )
