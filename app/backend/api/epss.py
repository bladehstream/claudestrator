"""
EPSS Enrichment API endpoints.

Provides manual triggering and status monitoring for EPSS enrichment.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.backend.database import AsyncSessionLocal, get_db
from app.backend.services.epss_enrichment import run_epss_enrichment
from app.backend.services.epss_scheduler import get_epss_scheduler

router = APIRouter(prefix="/admin/epss", tags=["EPSS Enrichment"])


class EPSSEnrichmentRequest(BaseModel):
    """Request to trigger EPSS enrichment."""
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum vulnerabilities to enrich")
    max_age_days: Optional[int] = Field(default=7, ge=1, le=365, description="Re-enrich scores older than this many days")


class EPSSEnrichmentResponse(BaseModel):
    """Response from EPSS enrichment."""
    processed: int
    enriched: int
    not_found: int
    errors: int
    message: str


class EPSSSchedulerStatusResponse(BaseModel):
    """EPSS scheduler status."""
    is_running: bool
    interval_hours: int
    batch_size: int
    max_age_days: int
    last_run: Optional[str]
    last_stats: Optional[dict]


@router.post("/trigger", response_model=EPSSEnrichmentResponse)
async def trigger_epss_enrichment(
    request: EPSSEnrichmentRequest,
    db = Depends(get_db)
):
    """
    Manually trigger EPSS enrichment for vulnerabilities.

    Enriches vulnerabilities that either:
    - Have never been enriched (epss_score is NULL)
    - Were enriched more than max_age_days ago

    Rate limiting is applied (1 request/second to FIRST.org API).
    """
    try:
        stats = await run_epss_enrichment(
            db=db,
            limit=request.limit,
            max_age_days=request.max_age_days
        )

        return EPSSEnrichmentResponse(
            processed=stats["processed"],
            enriched=stats["enriched"],
            not_found=stats["not_found"],
            errors=stats["errors"],
            message=f"Enrichment complete: {stats['enriched']} vulnerabilities enriched"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EPSS enrichment failed: {str(e)}")


@router.get("/status", response_model=EPSSSchedulerStatusResponse)
async def get_epss_scheduler_status():
    """
    Get EPSS scheduler status.

    Returns information about the background EPSS enrichment scheduler,
    including running status, configuration, and last run statistics.
    """
    scheduler = get_epss_scheduler()
    status = scheduler.get_status()

    return EPSSSchedulerStatusResponse(
        is_running=status["is_running"],
        interval_hours=status["interval_hours"],
        batch_size=status["batch_size"],
        max_age_days=status["max_age_days"],
        last_run=status["last_run"],
        last_stats=status["last_stats"]
    )


@router.post("/scheduler/start")
async def start_epss_scheduler_endpoint():
    """
    Start the EPSS enrichment scheduler.

    The scheduler will run enrichment cycles at the configured interval.
    """
    scheduler = get_epss_scheduler()

    if scheduler.is_running:
        raise HTTPException(status_code=400, detail="EPSS scheduler already running")

    scheduler.start()

    return {"message": "EPSS scheduler started", "interval_hours": scheduler.interval_hours}


@router.post("/scheduler/stop")
async def stop_epss_scheduler_endpoint():
    """
    Stop the EPSS enrichment scheduler.

    Gracefully stops the scheduler (waits for current cycle to complete).
    """
    scheduler = get_epss_scheduler()

    if not scheduler.is_running:
        raise HTTPException(status_code=400, detail="EPSS scheduler not running")

    await scheduler.stop()

    return {"message": "EPSS scheduler stopped"}


@router.post("/scheduler/trigger", response_model=EPSSEnrichmentResponse)
async def trigger_epss_scheduler_now():
    """
    Manually trigger EPSS scheduler to run immediately.

    Uses the scheduler's configured batch_size and max_age_days settings.
    """
    scheduler = get_epss_scheduler()

    try:
        stats = await scheduler.trigger_now()

        return EPSSEnrichmentResponse(
            processed=stats["processed"],
            enriched=stats["enriched"],
            not_found=stats["not_found"],
            errors=stats["errors"],
            message=f"Scheduler triggered: {stats['enriched']} vulnerabilities enriched"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scheduler trigger failed: {str(e)}")
