"""
Background processing service for converting raw entries to curated vulnerabilities.

This service:
- Polls raw_entries table for pending entries
- Uses LLM to extract structured data
- Deduplicates by CVE ID
- Moves to vulnerabilities table
- Purges old processed raw entries
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.models.database import (
    RawEntry, Vulnerability, LLMConfig, ProcessingStatus
)
from app.backend.services.llm_service import LLMService, ExtractionResult
from app.backend.services.ollama_client import OllamaClient, OllamaConnectionError, OllamaModelError

logger = logging.getLogger(__name__)


class ProcessingStats:
    """Statistics from a processing run."""

    def __init__(self):
        self.processed = 0
        self.created = 0
        self.updated = 0
        self.failed = 0
        self.skipped = 0
        self.duplicates = 0
        self.purged = 0
        self.started_at = datetime.utcnow()
        self.ended_at: Optional[datetime] = None

    def finish(self):
        """Mark processing as finished."""
        self.ended_at = datetime.utcnow()

    def duration_seconds(self) -> float:
        """Calculate processing duration."""
        end = self.ended_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "processed": self.processed,
            "created": self.created,
            "updated": self.updated,
            "failed": self.failed,
            "skipped": self.skipped,
            "duplicates": self.duplicates,
            "purged": self.purged,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds(),
        }


class ProcessingService:
    """
    Service for background processing of raw entries.

    Handles the entire pipeline from raw ingestion to curated vulnerabilities.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def get_llm_config(self) -> Optional[LLMConfig]:
        """Get active LLM configuration."""
        result = await self.db.execute(
            select(LLMConfig).order_by(LLMConfig.id.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_pending_entries(self, limit: Optional[int] = None) -> List[RawEntry]:
        """
        Get pending raw entries that need processing.

        Args:
            limit: Maximum number of entries to fetch (from config if None)

        Returns:
            List of raw entries with status PENDING or FAILED (with retry limit)
        """
        config = await self.get_llm_config()
        if limit is None and config:
            limit = config.batch_size
        if limit is None:
            limit = 10  # Default fallback

        # Get entries that are pending or failed (but not too many times)
        query = select(RawEntry).where(
            or_(
                RawEntry.processing_status == ProcessingStatus.PENDING.value,
                and_(
                    RawEntry.processing_status == ProcessingStatus.FAILED.value,
                    RawEntry.processing_attempts < 3  # Max retry attempts
                )
            )
        ).order_by(RawEntry.ingested_at).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def process_entry(
        self,
        entry: RawEntry,
        llm_service: LLMService,
        config: LLMConfig
    ) -> Optional[Vulnerability]:
        """
        Process a single raw entry.

        Args:
            entry: Raw entry to process
            llm_service: LLM service for extraction
            config: LLM configuration

        Returns:
            Created/updated vulnerability or None if extraction failed
        """
        try:
            # Mark as processing
            entry.processing_status = ProcessingStatus.PROCESSING.value
            entry.processing_attempts += 1
            await self.db.commit()

            # Extract vulnerability data
            extraction = await llm_service.extract_vulnerability(entry.raw_payload)

            if not extraction.cve_id:
                # No CVE ID found - mark as failed
                entry.processing_status = ProcessingStatus.FAILED.value
                entry.last_processing_error = "No CVE ID extracted from text"
                entry.processed_at = datetime.utcnow()
                await self.db.commit()
                logger.warning(f"Entry {entry.id}: No CVE ID found")
                return None

            # Check for duplicate vulnerability
            existing = await self.db.get(Vulnerability, extraction.cve_id)

            if existing:
                # Update existing vulnerability if confidence is higher
                if extraction.confidence_score > existing.confidence_score:
                    logger.info(
                        f"Entry {entry.id}: Updating CVE {extraction.cve_id} "
                        f"(confidence: {existing.confidence_score:.2f} -> {extraction.confidence_score:.2f})"
                    )

                    # Update fields
                    existing.title = extraction.title or existing.title
                    existing.description = extraction.description or existing.description
                    existing.severity = extraction.severity or existing.severity
                    existing.cvss_score = extraction.cvss_score or existing.cvss_score
                    existing.cvss_vector = extraction.cvss_vector or existing.cvss_vector
                    existing.confidence_score = extraction.confidence_score
                    existing.needs_review = extraction.needs_review
                    existing.extraction_metadata = extraction.extraction_metadata
                    existing.updated_at = datetime.utcnow()

                    entry.processing_status = ProcessingStatus.COMPLETED.value
                    entry.processed_at = datetime.utcnow()
                    await self.db.commit()
                    return existing
                else:
                    logger.info(
                        f"Entry {entry.id}: Skipping duplicate CVE {extraction.cve_id} "
                        f"(lower confidence: {extraction.confidence_score:.2f} vs {existing.confidence_score:.2f})"
                    )
                    entry.processing_status = ProcessingStatus.COMPLETED.value
                    entry.processed_at = datetime.utcnow()
                    await self.db.commit()
                    return None

            # Create new vulnerability
            vulnerability = Vulnerability(
                cve_id=extraction.cve_id,
                title=extraction.title,
                description=extraction.description,
                severity=extraction.severity,
                cvss_score=extraction.cvss_score,
                cvss_vector=extraction.cvss_vector,
                confidence_score=extraction.confidence_score,
                needs_review=extraction.needs_review,
                extraction_metadata=extraction.extraction_metadata,
            )

            self.db.add(vulnerability)
            entry.processing_status = ProcessingStatus.COMPLETED.value
            entry.processed_at = datetime.utcnow()
            await self.db.commit()

            logger.info(
                f"Entry {entry.id}: Created CVE {extraction.cve_id} "
                f"(confidence: {extraction.confidence_score:.2f}, review: {extraction.needs_review})"
            )
            return vulnerability

        except Exception as e:
            logger.error(f"Entry {entry.id}: Processing failed - {str(e)}")
            entry.processing_status = ProcessingStatus.FAILED.value
            entry.last_processing_error = str(e)
            entry.processed_at = datetime.utcnow()
            await self.db.commit()
            return None

    async def process_batch(self, batch_size: Optional[int] = None) -> ProcessingStats:
        """
        Process a batch of pending raw entries.

        Args:
            batch_size: Number of entries to process (from config if None)

        Returns:
            Statistics from processing run
        """
        stats = ProcessingStats()

        try:
            # Get LLM configuration
            config = await self.get_llm_config()
            if not config or not config.selected_model:
                logger.error("No LLM configuration found or no model selected")
                stats.finish()
                return stats

            # Initialize LLM service
            ollama_client = OllamaClient(
                base_url=config.ollama_base_url,
                timeout=30.0
            )

            try:
                # Test connection
                await ollama_client.test_connection()
            except OllamaConnectionError as e:
                logger.error(f"Cannot connect to Ollama: {e}")
                stats.finish()
                return stats

            llm_service = LLMService(
                ollama_client=ollama_client,
                model=config.selected_model,
                temperature=config.temperature,
                confidence_threshold=config.confidence_threshold,
            )

            # Get pending entries
            entries = await self.get_pending_entries(batch_size or config.batch_size)
            logger.info(f"Processing batch of {len(entries)} entries")

            # Process each entry
            for entry in entries:
                result = await self.process_entry(entry, llm_service, config)

                stats.processed += 1

                if result:
                    # Check if it was an update or new creation
                    if result.created_at == result.updated_at:
                        stats.created += 1
                    else:
                        stats.updated += 1
                        stats.duplicates += 1
                elif entry.processing_status == ProcessingStatus.FAILED.value:
                    stats.failed += 1
                else:
                    # Duplicate with lower confidence
                    stats.skipped += 1
                    stats.duplicates += 1

            stats.finish()
            logger.info(
                f"Batch processing complete: {stats.processed} processed, "
                f"{stats.created} created, {stats.updated} updated, "
                f"{stats.failed} failed, {stats.skipped} skipped"
            )

        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            stats.finish()

        return stats

    async def purge_old_entries(self, days: int = 7) -> int:
        """
        Purge processed raw entries older than specified days.

        Args:
            days: Age threshold in days (default: 7)

        Returns:
            Number of entries purged
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Delete entries that are processed and older than cutoff
        query = delete(RawEntry).where(
            and_(
                RawEntry.processing_status == ProcessingStatus.COMPLETED.value,
                RawEntry.processed_at < cutoff_date
            )
        )

        result = await self.db.execute(query)
        await self.db.commit()

        purged_count = result.rowcount
        logger.info(f"Purged {purged_count} raw entries older than {days} days")

        return purged_count

    async def get_processing_status(self) -> Dict[str, Any]:
        """
        Get current processing queue status.

        Returns:
            Dictionary with status information
        """
        # Count entries by status
        from sqlalchemy import func

        pending_count = await self.db.scalar(
            select(func.count()).select_from(RawEntry).where(
                RawEntry.processing_status == ProcessingStatus.PENDING.value
            )
        )

        processing_count = await self.db.scalar(
            select(func.count()).select_from(RawEntry).where(
                RawEntry.processing_status == ProcessingStatus.PROCESSING.value
            )
        )

        completed_count = await self.db.scalar(
            select(func.count()).select_from(RawEntry).where(
                RawEntry.processing_status == ProcessingStatus.COMPLETED.value
            )
        )

        failed_count = await self.db.scalar(
            select(func.count()).select_from(RawEntry).where(
                RawEntry.processing_status == ProcessingStatus.FAILED.value
            )
        )

        # Count vulnerabilities by review status
        total_vulns = await self.db.scalar(
            select(func.count()).select_from(Vulnerability)
        )

        needs_review = await self.db.scalar(
            select(func.count()).select_from(Vulnerability).where(
                Vulnerability.needs_review == True
            )
        )

        return {
            "raw_entries": {
                "pending": pending_count or 0,
                "processing": processing_count or 0,
                "completed": completed_count or 0,
                "failed": failed_count or 0,
                "total": (pending_count or 0) + (processing_count or 0) + (completed_count or 0) + (failed_count or 0),
            },
            "vulnerabilities": {
                "total": total_vulns or 0,
                "needs_review": needs_review or 0,
                "approved": (total_vulns or 0) - (needs_review or 0),
            },
        }
