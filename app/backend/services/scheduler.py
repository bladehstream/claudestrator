"""
Background scheduler for periodic processing of raw entries.

Runs processing jobs on a configurable interval and can be manually triggered.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.backend.database import AsyncSessionLocal
from app.backend.services.processing_service import ProcessingService, ProcessingStats

logger = logging.getLogger(__name__)


class ProcessingScheduler:
    """
    Background scheduler for processing raw entries.

    Runs on configurable interval (1-60 minutes) and supports manual triggering.
    """

    def __init__(self):
        """Initialize scheduler."""
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.last_run: Optional[datetime] = None
        self.last_stats: Optional[ProcessingStats] = None
        self._stop_event = asyncio.Event()

    async def get_interval_minutes(self) -> int:
        """Get processing interval from config."""
        async with AsyncSessionLocal() as db:
            service = ProcessingService(db)
            config = await service.get_llm_config()
            if config:
                return max(1, min(60, config.processing_interval_minutes))
            return 30  # Default fallback

    async def run_processing_cycle(self) -> ProcessingStats:
        """
        Run a single processing cycle.

        Returns:
            Statistics from the processing run
        """
        logger.info("Starting processing cycle")
        self.last_run = datetime.utcnow()

        async with AsyncSessionLocal() as db:
            service = ProcessingService(db)

            # Process batch
            stats = await service.process_batch()
            self.last_stats = stats

            # Purge old entries (7 days)
            purged = await service.purge_old_entries(days=7)
            stats.purged = purged

            logger.info(
                f"Processing cycle complete: {stats.processed} processed, "
                f"{stats.created} created, {stats.purged} purged, "
                f"duration: {stats.duration_seconds():.2f}s"
            )

        return stats

    async def _run_loop(self):
        """Internal loop that runs processing cycles."""
        logger.info("Processing scheduler started")

        while not self._stop_event.is_set():
            try:
                # Run processing cycle
                await self.run_processing_cycle()

                # Get interval for next run
                interval_minutes = await self.get_interval_minutes()
                interval_seconds = interval_minutes * 60

                logger.info(f"Next processing cycle in {interval_minutes} minutes")

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
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                # Wait a bit before retrying on error
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=60)
                    break
                except asyncio.TimeoutError:
                    continue

        logger.info("Processing scheduler stopped")

    def start(self):
        """Start the background scheduler."""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        self._stop_event.clear()
        self.is_running = True
        self.task = asyncio.create_task(self._run_loop())
        logger.info("Scheduler start requested")

    async def stop(self):
        """Stop the background scheduler."""
        if not self.is_running:
            logger.warning("Scheduler not running")
            return

        logger.info("Stopping scheduler...")
        self._stop_event.set()

        if self.task:
            try:
                await asyncio.wait_for(self.task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Scheduler did not stop gracefully, cancelling")
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass

        self.is_running = False
        self.task = None
        logger.info("Scheduler stopped")

    async def trigger_now(self) -> ProcessingStats:
        """
        Manually trigger a processing cycle immediately.

        Returns:
            Statistics from the processing run
        """
        logger.info("Manual processing trigger requested")
        return await self.run_processing_cycle()

    def get_status(self) -> dict:
        """
        Get scheduler status.

        Returns:
            Dictionary with status information
        """
        return {
            "is_running": self.is_running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_stats": self.last_stats.to_dict() if self.last_stats else None,
        }


# Global scheduler instance
_scheduler: Optional[ProcessingScheduler] = None


def get_scheduler() -> ProcessingScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ProcessingScheduler()
    return _scheduler


async def start_scheduler():
    """Start the global scheduler (called on app startup)."""
    scheduler = get_scheduler()
    scheduler.start()


async def stop_scheduler():
    """Stop the global scheduler (called on app shutdown)."""
    scheduler = get_scheduler()
    await scheduler.stop()
