"""
Data source polling service.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
import logging

from app.database.models import DataSource, RawEntry, HealthStatus, ProcessingStatus

logger = logging.getLogger(__name__)


def trigger_manual_poll(source_id: int, db: Session) -> bool:
    """
    Trigger a manual poll for a data source.

    In a full implementation, this would enqueue a background job.
    For MVP, we'll set the flag and return success.

    Args:
        source_id: ID of the source to poll
        db: Database session

    Returns:
        True if poll was triggered successfully, False otherwise
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        logger.error(f"Source {source_id} not found")
        return False

    if source.is_running:
        logger.warning(f"Source {source_id} is already running")
        return False

    # In production, this would:
    # 1. Enqueue a background job (Celery, APScheduler, etc.)
    # 2. The job would set is_running=True
    # 3. Poll the source
    # 4. Store results in RawEntry table
    # 5. Set is_running=False
    # 6. Update health status

    # For MVP, we just log and return success
    logger.info(f"Manual poll triggered for source {source_id}: {source.name}")

    # Update last poll time
    source.last_poll_at = datetime.utcnow()
    db.commit()

    return True


def poll_source(source_id: int, db: Session) -> dict:
    """
    Poll a data source and store raw entries.

    This is a placeholder for the actual polling logic.

    Args:
        source_id: ID of the source to poll
        db: Database session

    Returns:
        Dict with poll results
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        return {"success": False, "error": "Source not found"}

    # Acquire lock
    if source.is_running:
        return {"success": False, "error": "Source is already running"}

    try:
        source.is_running = True
        source.last_poll_at = datetime.utcnow()
        db.commit()

        # TODO: Implement actual polling logic based on source_type
        # For NVD: Use NVD API
        # For CISA KEV: Download JSON catalog
        # For RSS: Parse RSS feed
        # For API: Make HTTP request
        # For URL_SCRAPER: Fetch and parse HTML

        # Placeholder: Create a sample raw entry
        raw_entry = RawEntry(
            source_id=source_id,
            raw_payload={"sample": "data"},
            raw_text="Sample raw text from polling",
            external_id=f"sample-{datetime.utcnow().timestamp()}",
            processing_status=ProcessingStatus.PENDING
        )
        db.add(raw_entry)

        # Update health status
        source.last_success_at = datetime.utcnow()
        source.consecutive_failures = 0
        source.health_status = HealthStatus.HEALTHY
        source.last_error = None

        db.commit()

        return {"success": True, "entries_added": 1}

    except Exception as e:
        logger.error(f"Error polling source {source_id}: {str(e)}")

        # Update failure count and health status
        source.consecutive_failures += 1
        source.last_error = str(e)

        if source.consecutive_failures >= 20:
            source.health_status = HealthStatus.FAILED
        elif source.consecutive_failures >= 5:
            source.health_status = HealthStatus.WARNING
        else:
            source.health_status = HealthStatus.HEALTHY

        db.commit()

        return {"success": False, "error": str(e)}

    finally:
        # Release lock
        source.is_running = False
        db.commit()


def check_source_health(source_id: int, db: Session) -> dict:
    """
    Check the health of a data source.

    Args:
        source_id: ID of the source to check
        db: Database session

    Returns:
        Dict with health information
    """
    source = db.query(DataSource).filter(DataSource.id == source_id).first()

    if not source:
        return {"error": "Source not found"}

    return {
        "source_id": source.id,
        "source_name": source.name,
        "health_status": source.health_status.value,
        "is_running": source.is_running,
        "last_poll_at": source.last_poll_at.isoformat() if source.last_poll_at else None,
        "last_success_at": source.last_success_at.isoformat() if source.last_success_at else None,
        "consecutive_failures": source.consecutive_failures,
        "last_error": source.last_error
    }
