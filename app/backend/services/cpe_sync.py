"""
CPE Dictionary synchronization service.

Fetches the NVD CPE dictionary and imports/updates products in the inventory.
Runs weekly to keep the product database current.
"""
import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.models.product import Product, ProductSearchIndex, CPESyncLog
from app.backend.database import AsyncSessionLocal


class CPEParser:
    """
    Parser for CPE 2.3 formatted strings.

    CPE Format: cpe:2.3:part:vendor:product:version:update:edition:language:sw_edition:target_sw:target_hw:other
    Example: cpe:2.3:a:microsoft:windows_10:1909:*:*:*:*:*:*:*
    """

    CPE_PATTERN = re.compile(
        r'^cpe:2\.3:([aho\*]):([^:]+):([^:]+):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*)$'
    )

    @classmethod
    def parse(cls, cpe_uri: str) -> Optional[Dict[str, str]]:
        """
        Parse CPE 2.3 string into components.

        Returns dict with keys: part, vendor, product, version, update, edition,
        language, sw_edition, target_sw, target_hw, other
        """
        if not cpe_uri:
            return None

        match = cls.CPE_PATTERN.match(cpe_uri)
        if not match:
            return None

        return {
            'part': cls._decode_component(match.group(1)),
            'vendor': cls._decode_component(match.group(2)),
            'product': cls._decode_component(match.group(3)),
            'version': cls._decode_component(match.group(4)),
            'update': cls._decode_component(match.group(5)),
            'edition': cls._decode_component(match.group(6)),
            'language': cls._decode_component(match.group(7)),
            'sw_edition': cls._decode_component(match.group(8)),
            'target_sw': cls._decode_component(match.group(9)),
            'target_hw': cls._decode_component(match.group(10)),
            'other': cls._decode_component(match.group(11)),
        }

    @staticmethod
    def _decode_component(component: str) -> Optional[str]:
        """
        Decode CPE component, handling wildcards and special characters.

        * or - or empty = None (any/not applicable)
        """
        if not component or component in ('*', '-', 'ANY', 'NA'):
            return None

        # Unescape special CPE characters
        component = component.replace('\\:', ':')
        component = component.replace('\\\\', '\\')

        return component.strip().lower()


class CPESyncService:
    """
    Service for syncing NVD CPE dictionary into product inventory.

    Handles:
    - Fetching CPE data from NVD API
    - Parsing CPE 2.3 format
    - Upserting products into database
    - Maintaining search index
    - Tracking sync history
    """

    NVD_CPE_API_URL = "https://services.nvd.nist.gov/rest/json/cpes/2.0"
    RESULTS_PER_PAGE = 2000  # NVD API max
    RATE_LIMIT_DELAY = 0.6  # 6 seconds per 10 requests = 0.6s per request

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CPE sync service.

        Args:
            api_key: Optional NVD API key for higher rate limits
        """
        self.api_key = api_key
        self.parser = CPEParser()

    async def sync_cpe_dictionary(self, start_index: int = 0, max_results: Optional[int] = None) -> CPESyncLog:
        """
        Fetch and sync CPE dictionary from NVD.

        Args:
            start_index: Starting index for pagination (default: 0)
            max_results: Maximum number of CPEs to fetch (None = all)

        Returns:
            CPESyncLog record with sync statistics
        """
        async with AsyncSessionLocal() as db:
            # Create sync log entry
            sync_log = CPESyncLog(
                started_at=datetime.utcnow(),
                status='running'
            )
            db.add(sync_log)
            await db.commit()
            await db.refresh(sync_log)

            try:
                # Fetch CPE data from NVD
                products_added = 0
                products_updated = 0
                products_deprecated = 0

                async with httpx.AsyncClient(timeout=30.0) as client:
                    current_index = start_index
                    total_results = None

                    while True:
                        # Build request parameters
                        params = {
                            'startIndex': current_index,
                            'resultsPerPage': self.RESULTS_PER_PAGE
                        }

                        # Add API key if provided
                        headers = {}
                        if self.api_key:
                            headers['apiKey'] = self.api_key

                        # Fetch page of results
                        try:
                            response = await client.get(
                                self.NVD_CPE_API_URL,
                                params=params,
                                headers=headers
                            )
                            response.raise_for_status()
                            data = response.json()
                        except httpx.HTTPError as e:
                            raise Exception(f"NVD API request failed: {str(e)}")

                        # Parse response
                        if total_results is None:
                            total_results = data.get('totalResults', 0)
                            sync_log.total_results = total_results

                        products = data.get('products', [])
                        if not products:
                            break

                        # Process products
                        for product_data in products:
                            cpe_item = product_data.get('cpe', {})
                            cpe_uri = cpe_item.get('cpeName')

                            if not cpe_uri:
                                continue

                            # Parse CPE
                            parsed = self.parser.parse(cpe_uri)
                            if not parsed:
                                continue

                            # Upsert product
                            action = await self._upsert_product(
                                db,
                                cpe_uri=cpe_uri,
                                parsed_cpe=parsed,
                                cpe_item=cpe_item
                            )

                            if action == 'added':
                                products_added += 1
                            elif action == 'updated':
                                products_updated += 1

                        # Update progress
                        current_index += len(products)

                        # Check if we should continue
                        if max_results and current_index >= (start_index + max_results):
                            break

                        if current_index >= total_results:
                            break

                        # Rate limiting
                        await asyncio.sleep(self.RATE_LIMIT_DELAY)

                # Mark deprecated products (products that disappeared from NVD)
                # products_deprecated = await self._mark_deprecated_products(db, sync_log.started_at)

                # Update sync log
                sync_log.completed_at = datetime.utcnow()
                sync_log.status = 'success'
                sync_log.products_added = products_added
                sync_log.products_updated = products_updated
                sync_log.products_deprecated = products_deprecated
                sync_log.nvd_timestamp = datetime.utcnow()

                await db.commit()

                return sync_log

            except Exception as e:
                # Mark sync as failed
                sync_log.completed_at = datetime.utcnow()
                sync_log.status = 'failed'
                sync_log.error_message = str(e)
                await db.commit()

                raise

    async def _upsert_product(
        self,
        db: AsyncSession,
        cpe_uri: str,
        parsed_cpe: Dict[str, str],
        cpe_item: Dict
    ) -> str:
        """
        Insert or update a product from CPE data.

        Returns:
            'added' if new product, 'updated' if existing product, 'skipped' if no change
        """
        vendor = parsed_cpe.get('vendor')
        product_name = parsed_cpe.get('product')

        if not vendor or not product_name:
            return 'skipped'

        # Get description from CPE item
        titles = cpe_item.get('titles', [])
        description = None
        if titles:
            # Prefer English description
            for title in titles:
                if title.get('lang') == 'en':
                    description = title.get('title')
                    break
            if not description and titles:
                description = titles[0].get('title')

        # Check if product exists
        result = await db.execute(
            select(Product).where(Product.cpe_uri == cpe_uri)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing product
            existing.vendor = vendor
            existing.product_name = product_name
            existing.version = parsed_cpe.get('version')
            existing.part = parsed_cpe.get('part')
            existing.description = description or existing.description
            existing.last_synced_at = datetime.utcnow()
            existing.deprecated = False  # Mark as active
            existing.updated_at = datetime.utcnow()

            await db.commit()
            await self._update_search_index(db, existing)

            return 'updated'
        else:
            # Create new product
            product = Product(
                cpe_uri=cpe_uri,
                vendor=vendor,
                product_name=product_name,
                version=parsed_cpe.get('version'),
                part=parsed_cpe.get('part'),
                description=description,
                source='nvd_cpe',
                is_monitored=False,  # Default to not monitored
                last_synced_at=datetime.utcnow()
            )

            db.add(product)
            await db.commit()
            await db.refresh(product)
            await self._update_search_index(db, product)

            return 'added'

    async def _update_search_index(self, db: AsyncSession, product: Product):
        """Update FTS5 search index for a product."""
        search_text = f"{product.vendor} {product.product_name}"
        if product.description:
            search_text += f" {product.description}"
        if product.cpe_uri:
            search_text += f" {product.cpe_uri}"

        # Check if index entry exists
        result = await db.execute(
            select(ProductSearchIndex).where(ProductSearchIndex.product_id == product.id)
        )
        index_entry = result.scalar_one_or_none()

        if index_entry:
            index_entry.vendor = product.vendor
            index_entry.product_name = product.product_name
            index_entry.description = product.description
            index_entry.search_text = search_text
        else:
            index_entry = ProductSearchIndex(
                product_id=product.id,
                vendor=product.vendor,
                product_name=product.product_name,
                description=product.description,
                search_text=search_text
            )
            db.add(index_entry)

        await db.commit()

    async def _mark_deprecated_products(self, db: AsyncSession, sync_time: datetime) -> int:
        """
        Mark products as deprecated if they haven't been synced recently.

        Products not updated in this sync are considered deprecated by NVD.
        """
        result = await db.execute(
            select(Product).where(
                Product.source == 'nvd_cpe',
                Product.last_synced_at < sync_time,
                Product.deprecated == False
            )
        )
        products = result.scalars().all()

        count = 0
        for product in products:
            product.deprecated = True
            product.updated_at = datetime.utcnow()
            count += 1

        if count > 0:
            await db.commit()

        return count


# Background job function for APScheduler
async def run_cpe_sync_job(api_key: Optional[str] = None):
    """
    Background job to sync CPE dictionary.

    Scheduled to run weekly to keep product inventory current.
    """
    service = CPESyncService(api_key=api_key)
    try:
        sync_log = await service.sync_cpe_dictionary()
        print(f"CPE sync completed: {sync_log.products_added} added, {sync_log.products_updated} updated")
        return sync_log
    except Exception as e:
        print(f"CPE sync failed: {str(e)}")
        raise
