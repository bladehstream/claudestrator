"""
Email notification scheduler.

Background scheduler for:
- Sending pending alert emails
- Sending periodic digest emails
- Tracking vulnerability alerts
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.backend.database import AsyncSessionLocal
from app.backend.services.email_notification_service import EmailNotificationService

logger = logging.getLogger(__name__)


class EmailScheduler:
    """
    Background scheduler for email notifications.

    Manages pending alert sending and periodic digest emails.
    """

    def __init__(
        self,
        pending_alert_interval_minutes: int = 5,
        digest_interval_hours: int = 24,
        digest_batch_size: int = 50
    ):
        """
        Initialize email scheduler.

        Args:
            pending_alert_interval_minutes: Minutes between pending alert checks
            digest_interval_hours: Hours between digest email sends
            digest_batch_size: Maximum alerts to send per batch
        """
        self.pending_alert_interval_minutes = max(1, min(60, pending_alert_interval_minutes))
        self.digest_interval_hours = max(1, min(168, digest_interval_hours))
        self.digest_batch_size = max(10, min(500, digest_batch_size))

        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.last_pending_send: Optional[datetime] = None
        self.last_digest_send: Optional[datetime] = None
        self.stats: dict = {}
        self._stop_event = asyncio.Event()
        self.email_service = EmailNotificationService()

    async def send_pending_alerts(self) -> dict:
        """
        Send all pending alert emails.

        Returns:
            Statistics from sending
        """
        logger.info("Starting pending alert send cycle")
        self.last_pending_send = datetime.utcnow()

        try:
            async with AsyncSessionLocal() as db:
                stats = await self.email_service.send_pending_alerts(
                    db,
                    max_batch_size=self.digest_batch_size
                )

                logger.info(
                    f"Pending alert send cycle complete: {stats['sent']} sent, "
                    f"{stats['failed']} failed, {stats['total']} total"
                )

                return stats

        except Exception as e:
            logger.error(f"Error in pending alert send cycle: {e}", exc_info=True)
            return {
                "total": 0,
                "sent": 0,
                "failed": 0,
                "error": str(e)
            }

    async def send_digest_emails(self) -> dict:
        """
        Send periodic digest emails.

        Returns:
            Statistics from digest sending
        """
        logger.info("Starting digest email send cycle")
        self.last_digest_send = datetime.utcnow()

        try:
            async with AsyncSessionLocal() as db:
                result = await self.email_service.send_digest_email(
                    db,
                    hours=self.digest_interval_hours
                )

                if result["success"]:
                    logger.info(f"Digest email sent successfully: {result}")
                else:
                    logger.warning(f"Digest email send failed: {result}")

                return result

        except Exception as e:
            logger.error(f"Error in digest send cycle: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e)
            }

    async def _run_loop(self):
        """Internal loop that runs email cycles."""
        logger.info(
            f"Email scheduler started (pending: {self.pending_alert_interval_minutes}m, "
            f"digest: {self.digest_interval_hours}h)"
        )

        while not self._stop_event.is_set():
            try:
                # Send pending alerts
                pending_stats = await self.send_pending_alerts()
                self.stats = pending_stats

                # Check if we should send digest
                if self.last_digest_send is None or \
                   (datetime.utcnow() - self.last_digest_send).total_seconds() >= \
                   (self.digest_interval_hours * 3600):
                    digest_result = await self.send_digest_emails()
                    self.stats.update(digest_result)

                # Calculate next check interval
                pending_seconds = self.pending_alert_interval_minutes * 60
                logger.info(f"Next pending alert check in {self.pending_alert_interval_minutes} minutes")

                # Wait for next cycle or stop signal
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=pending_seconds
                    )
                    # Stop signal received
                    break
                except asyncio.TimeoutError:
                    # Continue loop
                    continue

            except Exception as e:
                logger.error(f"Error in email scheduler loop: {e}", exc_info=True)
                # Wait before retrying
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=60  # Retry after 1 minute on error
                    )
                    break
                except asyncio.TimeoutError:
                    continue

    async def start(self):
        """Start the email scheduler."""
        if self.is_running:
            logger.warning("Email scheduler already running")
            return

        self.is_running = True
        self._stop_event.clear()
        self.task = asyncio.create_task(self._run_loop())
        logger.info("Email scheduler started")

    async def stop(self):
        """Gracefully stop the email scheduler."""
        if not self.is_running:
            logger.warning("Email scheduler not running")
            return

        logger.info("Stopping email scheduler...")
        self._stop_event.set()

        if self.task and not self.task.done():
            try:
                await asyncio.wait_for(self.task, timeout=10)
            except asyncio.TimeoutError:
                logger.warning("Email scheduler did not stop gracefully, cancelling")
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass

        self.is_running = False
        logger.info("Email scheduler stopped")

    async def trigger_pending_alerts(self) -> dict:
        """Manually trigger pending alert sending."""
        return await self.send_pending_alerts()

    async def trigger_digest(self) -> dict:
        """Manually trigger digest email sending."""
        return await self.send_digest_emails()

    def get_status(self) -> dict:
        """Get current scheduler status."""
        return {
            "is_running": self.is_running,
            "last_pending_send": self.last_pending_send.isoformat() if self.last_pending_send else None,
            "last_digest_send": self.last_digest_send.isoformat() if self.last_digest_send else None,
            "pending_alert_interval_minutes": self.pending_alert_interval_minutes,
            "digest_interval_hours": self.digest_interval_hours,
            "last_stats": self.stats
        }


# Global scheduler instance
_email_scheduler: Optional[EmailScheduler] = None


async def get_email_scheduler() -> EmailScheduler:
    """Get or create global email scheduler instance."""
    global _email_scheduler
    if _email_scheduler is None:
        _email_scheduler = EmailScheduler()
    return _email_scheduler


async def start_email_scheduler():
    """Start global email scheduler."""
    scheduler = await get_email_scheduler()
    await scheduler.start()


async def stop_email_scheduler():
    """Stop global email scheduler."""
    scheduler = await get_email_scheduler()
    await scheduler.stop()
