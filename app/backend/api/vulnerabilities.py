"""
Vulnerability data API routes.

Provides endpoints for:
- Fetching vulnerability trend data (time series)
- Filtering vulnerabilities by various criteria
- Dashboard statistics
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.database import get_db
from app.backend.models.database import Vulnerability

router = APIRouter(prefix="/api/vulnerabilities", tags=["vulnerabilities"])


# Response Models
class TrendDataPoint(BaseModel):
    """Single data point in the trend chart."""
    date: str  # ISO date string (YYYY-MM-DD)
    count: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class TrendChartResponse(BaseModel):
    """Response model for trend chart data."""
    data_points: List[TrendDataPoint]
    total_count: int
    date_range_start: str
    date_range_end: str
    filters_applied: dict


class VulnerabilityStatsResponse(BaseModel):
    """Response model for dashboard statistics."""
    total_vulnerabilities: int
    kev_count: int
    high_epss_count: int
    new_this_week: int
    by_severity: dict
    by_kev_status: dict


@router.get("/trends", response_model=TrendChartResponse)
async def get_vulnerability_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in trend"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    kev_only: bool = Query(False, description="Only include KEV vulnerabilities"),
    epss_threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum EPSS score"),
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get vulnerability trend data over time.

    Returns daily counts of vulnerabilities, broken down by severity.
    Supports filtering by severity, KEV status, EPSS threshold, and vendor.
    """
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    # Build filter conditions
    filters = [
        Vulnerability.published_date.isnot(None),
        func.date(Vulnerability.published_date) >= start_date,
        func.date(Vulnerability.published_date) <= end_date
    ]

    if severity:
        filters.append(Vulnerability.severity == severity.upper())

    if kev_only:
        filters.append(Vulnerability.kev_status == True)

    if epss_threshold is not None:
        filters.append(Vulnerability.epss_score >= epss_threshold)

    # Note: Vendor filtering requires joining with products table
    # For MVP, we'll handle this in a future iteration

    # Query vulnerabilities grouped by date and severity
    query = select(
        func.date(Vulnerability.published_date).label('date'),
        func.count().label('total'),
        func.sum(func.case((Vulnerability.severity == 'CRITICAL', 1), else_=0)).label('critical'),
        func.sum(func.case((Vulnerability.severity == 'HIGH', 1), else_=0)).label('high'),
        func.sum(func.case((Vulnerability.severity == 'MEDIUM', 1), else_=0)).label('medium'),
        func.sum(func.case((Vulnerability.severity == 'LOW', 1), else_=0)).label('low')
    ).where(
        and_(*filters)
    ).group_by(
        func.date(Vulnerability.published_date)
    ).order_by(
        func.date(Vulnerability.published_date)
    )

    result = await db.execute(query)
    rows = result.all()

    # Create a complete date range (fill gaps with zeros)
    date_map = {}
    for row in rows:
        date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
        date_map[date_str] = TrendDataPoint(
            date=date_str,
            count=int(row.total),
            critical=int(row.critical or 0),
            high=int(row.high or 0),
            medium=int(row.medium or 0),
            low=int(row.low or 0)
        )

    # Fill in missing dates with zero counts
    data_points = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        if date_str in date_map:
            data_points.append(date_map[date_str])
        else:
            data_points.append(TrendDataPoint(
                date=date_str,
                count=0,
                critical=0,
                high=0,
                medium=0,
                low=0
            ))
        current_date += timedelta(days=1)

    total_count = sum(dp.count for dp in data_points)

    return TrendChartResponse(
        data_points=data_points,
        total_count=total_count,
        date_range_start=start_date.isoformat(),
        date_range_end=end_date.isoformat(),
        filters_applied={
            "days": days,
            "severity": severity,
            "kev_only": kev_only,
            "epss_threshold": epss_threshold,
            "vendor": vendor
        }
    )


@router.get("/stats", response_model=VulnerabilityStatsResponse)
async def get_vulnerability_stats(
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    kev_only: bool = Query(False, description="Only include KEV vulnerabilities"),
    epss_threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum EPSS score"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Filter by published date within last N days"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard statistics for vulnerabilities.

    Returns counts for KPIs: total vulnerabilities, KEV count, high EPSS, new this week.
    Supports filtering by severity, KEV status, EPSS threshold, and date range.
    """
    # Build base filter conditions
    base_filters = []

    if severity:
        base_filters.append(Vulnerability.severity == severity.upper())

    if kev_only:
        base_filters.append(Vulnerability.kev_status == True)

    if epss_threshold is not None:
        base_filters.append(Vulnerability.epss_score >= epss_threshold)

    if days is not None:
        date_threshold = datetime.utcnow() - timedelta(days=days)
        base_filters.append(Vulnerability.published_date >= date_threshold)

    # Total vulnerabilities
    total_query = select(func.count()).select_from(Vulnerability)
    if base_filters:
        total_query = total_query.where(and_(*base_filters))
    total_result = await db.execute(total_query)
    total_vulnerabilities = total_result.scalar() or 0

    # KEV count (within filtered set)
    kev_filters = base_filters.copy()
    if not kev_only:  # If not already filtering by KEV, add it
        kev_filters.append(Vulnerability.kev_status == True)
    kev_query = select(func.count()).select_from(Vulnerability)
    if kev_filters:
        kev_query = kev_query.where(and_(*kev_filters))
    kev_result = await db.execute(kev_query)
    kev_count = kev_result.scalar() or 0

    # High EPSS (> 0.7) within filtered set
    epss_filters = base_filters.copy()
    epss_filters.append(Vulnerability.epss_score >= 0.7)
    high_epss_query = select(func.count()).select_from(Vulnerability).where(and_(*epss_filters))
    high_epss_result = await db.execute(high_epss_query)
    high_epss_count = high_epss_result.scalar() or 0

    # New this week (within filtered set, excluding days filter)
    week_filters = [f for f in base_filters if not (hasattr(f, 'left') and hasattr(f.left, 'key') and f.left.key == 'published_date')]
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_filters.append(Vulnerability.published_date >= week_ago)
    new_week_query = select(func.count()).select_from(Vulnerability).where(and_(*week_filters))
    new_week_result = await db.execute(new_week_query)
    new_this_week = new_week_result.scalar() or 0

    # By severity (within filtered set)
    severity_query = select(
        Vulnerability.severity,
        func.count().label('count')
    ).group_by(Vulnerability.severity)
    if base_filters:
        severity_query = severity_query.where(and_(*base_filters))
    severity_result = await db.execute(severity_query)
    by_severity = {row.severity or 'UNKNOWN': row.count for row in severity_result}

    # By KEV status (within filtered set)
    by_kev_status = {
        "kev": kev_count,
        "non_kev": total_vulnerabilities - kev_count
    }

    return VulnerabilityStatsResponse(
        total_vulnerabilities=total_vulnerabilities,
        kev_count=kev_count,
        high_epss_count=high_epss_count,
        new_this_week=new_this_week,
        by_severity=by_severity,
        by_kev_status=by_kev_status
    )
