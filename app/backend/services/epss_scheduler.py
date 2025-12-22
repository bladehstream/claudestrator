"""
EPSS Enrichment Scheduler.

Background scheduler for periodic EPSS enrichment of vulnerabilities.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.backend.database import AsyncSessionLocal
from app.backend.services.epss_enrichment import run_epss_enrichment

logger = logging.getLogger(__name__)


class EPSSScheduler:
    """
    Background scheduler for EPSS enrichment.

    Runs EPSS enrichment on a configurable interval.
    """

    def __init__(
        self,
        interval_hours: int = 24,
        batch_size: int = 100,
        max_age_days: int = 7
    ):
        """
        Initialize EPSS scheduler.

        Args:
            interval_hours: Hours between enrichment runs (default: 24)
            batch_size: Maximum vulnerabilities to enrich per run
            max_age_days: Re-enrich scores older than this many days
        """
        self.interval_hours = max(1, min(168, interval_hours))  # 1 hour to 1 week
        self.batch_size = max(1, min(1000, batch_size))
        self.max_age_days = max_age_days

        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.last_run: Optional[datetime] = None
        self.last_stats: Optional[dict] = None
        self._stop_event = asyncio.Event()

    async def run_enrichment_cycle(self) -> dict:
        """
        Run a single EPSS enrichment cycle.

        Returns:
            Statistics from the enrichment run
        """
        logger.info("Starting EPSS enrichment cycle")
        self.last_run = datetime.utcnow()

        try:
            async with AsyncSessionLocal() as db:
                stats = await run_epss_enrichment(
                    db=db,
                    limit=self.batch_size,
                    max_age_days=self.max_age_days
                )
                self.last_stats = stats

                logger.info(
                    f"EPSS enrichment cycle complete: {stats['enriched']} enriched, "
                    f"{stats['not_found']} not found, {stats['errors']} errors"
                )

                return stats

        except Exception as e:
            logger.error(f"Error in EPSS enrichment cycle: {e}", exc_info=True)
            error_stats = {
                "processed": 0,
                "enriched": 0,
                "not_found": 0,
                "errors": 1,
                "error_message": str(e)
            }
            self.last_stats = error_stats
            return error_stats

    async def _run_loop(self):
        """Internal loop that runs enrichment cycles."""
        logger.info(f"EPSS scheduler started (interval: {self.interval_hours}h, batch: {self.batch_size})")

        while not self._stop_event.is_set():
            try:
                # Run enrichment cycle
                await self.run_enrichment_cycle()

                # Calculate interval
                interval_seconds = self.interval_hours * 3600

                logger.info(f"Next EPSS enrichment cycle in {self.interval_hours} hours")

                # Wait for interval or stop signal
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=interval_seconds
                    )
                    # If we get here, stop was requested
                    break
                except asyncio.TimeoutError:
                    # Timeout is normal - continue to next cycle
                    continue

            except Exception as e:
                logger.error(f"Error in EPSS scheduler loop: {e}", exc_info=True)
                # Wait a bit before retrying on error (1 hour)
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=3600)
                    break
                except asyncio.TimeoutError:
                    continue

        logger.info("EPSS scheduler stopped")

    def start(self):
        """Start the background scheduler."""
        if self.is_running:
            logger.warning("EPSS scheduler already running")
            return

        self._stop_event.clear()
        self.is_running = True
        self.task = asyncio.create_task(self._run_loop())
        logger.info("EPSS scheduler start requested")

    async def stop(self):
        """Stop the background scheduler."""
        if not self.is_running:
            logger.warning("EPSS scheduler not running")
            return

        logger.info("Stopping EPSS scheduler...")
        self._stop_event.set()

        if self.task:
            try:
                await asyncio.wait_for(self.task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("EPSS scheduler did not stop gracefully, cancelling")
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass

        self.is_running = False
        self.task = None
        logger.info("EPSS scheduler stopped")

    async def trigger_now(self) -> dict:
        """
        Manually trigger an enrichment cycle immediately.

        Returns:
            Statistics from the enrichment run
        """
        logger.info("Manual EPSS enrichment trigger requested")
        return await self.run_enrichment_cycle()

    def get_status(self) -> dict:
        """
        Get scheduler status.

        Returns:
            Dictionary with status information
        """
        return {
            "is_running": self.is_running,
            "interval_hours": self.interval_hours,
            "batch_size": self.batch_size,
            "max_age_days": self.max_age_days,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_stats": self.last_stats,
        }


# Global scheduler instance
_epss_scheduler: Optional[EPSSScheduler] = None


def get_epss_scheduler(
    interval_hours: int = 24,
    batch_size: int = 100,
    max_age_days: int = 7
) -> EPSSScheduler:
    """
    Get the global EPSS scheduler instance.

    Args:
        interval_hours: Hours between enrichment runs
        batch_size: Maximum vulnerabilities to enrich per run
        max_age_days: Re-enrich scores older than this many days

    Returns:
        EPSSScheduler instance
    """
    global _epss_scheduler
    if _epss_scheduler is None:
        _epss_scheduler = EPSSScheduler(
            interval_hours=interval_hours,
            batch_size=batch_size,
            max_age_days=max_age_days
        )
    return _epss_scheduler


async def start_epss_scheduler():
    """Start the global EPSS scheduler (called on app startup)."""
    scheduler = get_epss_scheduler()
    scheduler.start()


async def stop_epss_scheduler():
    """Stop the global EPSS scheduler (called on app shutdown)."""
    scheduler = get_epss_scheduler()
    await scheduler.stop()
