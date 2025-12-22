"""
API endpoints for background processing management.

Provides endpoints for:
- Manual processing trigger
- Scheduler control (start/stop)
- Processing status
- Purge operations
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.database import get_db
from app.backend.services.processing_service import ProcessingService
from app.backend.services.scheduler import get_scheduler

router = APIRouter(prefix="/admin/processing", tags=["Processing"])


# Request/Response Models

class ProcessingStatsResponse(BaseModel):
    """Response model for processing statistics."""
    processed: int = Field(..., description="Total entries processed")
    created: int = Field(..., description="New vulnerabilities created")
    updated: int = Field(..., description="Existing vulnerabilities updated")
    failed: int = Field(..., description="Entries that failed processing")
    skipped: int = Field(..., description="Entries skipped (duplicate with lower confidence)")
    duplicates: int = Field(..., description="Total duplicates found")
    purged: int = Field(..., description="Old raw entries purged")
    started_at: str = Field(..., description="Processing start timestamp (ISO)")
    ended_at: Optional[str] = Field(None, description="Processing end timestamp (ISO)")
    duration_seconds: float = Field(..., description="Processing duration in seconds")


class TriggerProcessingResponse(BaseModel):
    """Response from manual processing trigger."""
    message: str
    stats: ProcessingStatsResponse


class SchedulerStatusResponse(BaseModel):
    """Response with scheduler status."""
    is_running: bool = Field(..., description="Whether scheduler is running")
    last_run: Optional[str] = Field(None, description="Last run timestamp (ISO)")
    last_stats: Optional[ProcessingStatsResponse] = Field(None, description="Last processing stats")


class ProcessingStatusResponse(BaseModel):
    """Response with overall processing status."""
    raw_entries: Dict[str, int] = Field(..., description="Raw entry counts by status")
    vulnerabilities: Dict[str, int] = Field(..., description="Vulnerability counts")


class PurgeRequest(BaseModel):
    """Request to purge old raw entries."""
    days: int = Field(7, ge=1, le=90, description="Age threshold in days")


class PurgeResponse(BaseModel):
    """Response from purge operation."""
    message: str
    purged_count: int = Field(..., description="Number of entries purged")


# Endpoints

@router.post("/trigger", response_model=TriggerProcessingResponse)
async def trigger_processing(db: AsyncSession = Depends(get_db)):
    """
    Manually trigger a processing cycle immediately.

    This will process pending raw entries using the configured LLM,
    create/update vulnerabilities, and purge old entries.

    **Note:** This runs independently of the scheduler.
    """
    scheduler = get_scheduler()

    try:
        stats = await scheduler.trigger_now()

        return TriggerProcessingResponse(
            message="Processing cycle completed successfully",
            stats=ProcessingStatsResponse(**stats.to_dict())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/status", response_model=ProcessingStatusResponse)
async def get_processing_status(db: AsyncSession = Depends(get_db)):
    """
    Get current processing queue status.

    Returns counts of raw entries by status and vulnerability statistics.
    """
    service = ProcessingService(db)
    status = await service.get_processing_status()

    return ProcessingStatusResponse(**status)


@router.get("/scheduler", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """
    Get background scheduler status.

    Returns whether the scheduler is running and last execution details.
    """
    scheduler = get_scheduler()
    status = scheduler.get_status()

    response_data = {
        "is_running": status["is_running"],
        "last_run": status["last_run"],
        "last_stats": None
    }

    if status["last_stats"]:
        response_data["last_stats"] = ProcessingStatsResponse(**status["last_stats"])

    return SchedulerStatusResponse(**response_data)


@router.post("/scheduler/start")
async def start_scheduler():
    """
    Start the background processing scheduler.

    The scheduler will run processing cycles at the configured interval.
    """
    scheduler = get_scheduler()

    if scheduler.is_running:
        raise HTTPException(status_code=400, detail="Scheduler is already running")

    scheduler.start()

    return {"message": "Scheduler started successfully"}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """
    Stop the background processing scheduler.

    Any currently running cycle will complete before stopping.
    """
    scheduler = get_scheduler()

    if not scheduler.is_running:
        raise HTTPException(status_code=400, detail="Scheduler is not running")

    await scheduler.stop()

    return {"message": "Scheduler stopped successfully"}


@router.post("/purge", response_model=PurgeResponse)
async def purge_old_entries(
    request: PurgeRequest = PurgeRequest(),
    db: AsyncSession = Depends(get_db)
):
    """
    Purge processed raw entries older than specified days.

    Only removes entries with status 'completed'. Pending and failed
    entries are retained for potential reprocessing.

    **Default:** 7 days
    **Range:** 1-90 days
    """
    service = ProcessingService(db)

    try:
        purged_count = await service.purge_old_entries(days=request.days)

        return PurgeResponse(
            message=f"Successfully purged entries older than {request.days} days",
            purged_count=purged_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Purge failed: {str(e)}")
