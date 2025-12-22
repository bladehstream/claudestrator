"""
Dashboard fragment routes for HTMX partial updates.

Serves HTML fragments for dashboard components like trend charts.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os
import httpx

from app.backend.database import get_db

router = APIRouter(prefix="/fragments", tags=["dashboard-fragments"])

# Setup templates
templates_path = os.path.join(os.path.dirname(__file__), "../../frontend/templates")
templates = Jinja2Templates(directory=templates_path)


@router.get("/trend-chart", response_class=HTMLResponse)
async def trend_chart_fragment(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    severity: Optional[str] = Query(None),
    kev_only: bool = Query(False),
    epss_threshold: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Serve the trend chart HTML fragment with data.

    This endpoint fetches trend data from the API and renders the chart fragment.
    Used for HTMX partial updates when filters change.
    """
    # Build API URL
    api_url = f"http://localhost:8000/api/vulnerabilities/trends?days={days}"

    if severity:
        api_url += f"&severity={severity}"
    if kev_only:
        api_url += "&kev_only=true"
    if epss_threshold is not None:
        api_url += f"&epss_threshold={epss_threshold}"

    # Fetch data from API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url, timeout=10.0)
            response.raise_for_status()
            chart_data = response.json()
        except Exception as e:
            # Return error state
            chart_data = {
                "data_points": [],
                "total_count": 0,
                "date_range_start": datetime.utcnow().isoformat(),
                "date_range_end": datetime.utcnow().isoformat(),
                "filters_applied": {"days": days, "error": str(e)}
            }

    return templates.TemplateResponse(
        "fragments/trend_chart.html",
        {
            "request": request,
            "chart_data": chart_data,
            "data": chart_data  # For template compatibility
        }
    )


@router.get("/kpi-cards", response_class=HTMLResponse)
async def kpi_cards_fragment(
    request: Request,
    severity: Optional[str] = Query(None),
    kev_only: bool = Query(False),
    epss_threshold: Optional[float] = Query(None),
    days: Optional[int] = Query(None, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Serve the KPI cards HTML fragment with filtered statistics.

    This endpoint fetches stats data from the API and renders the KPI cards fragment.
    Used for HTMX partial updates when filters change.
    """
    # Build API URL
    api_url = "http://localhost:8000/api/vulnerabilities/stats?"
    params = []

    if severity:
        params.append(f"severity={severity}")
    if kev_only:
        params.append("kev_only=true")
    if epss_threshold is not None:
        params.append(f"epss_threshold={epss_threshold}")
    if days is not None:
        params.append(f"days={days}")

    api_url += "&".join(params)

    # Fetch data from API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url, timeout=10.0)
            response.raise_for_status()
            stats = response.json()
        except Exception as e:
            # Return error state
            stats = {
                "total_vulnerabilities": 0,
                "kev_count": 0,
                "high_epss_count": 0,
                "new_this_week": 0,
                "by_severity": {},
                "by_kev_status": {}
            }

    return templates.TemplateResponse(
        "fragments/kpi_cards.html",
        {
            "request": request,
            "stats": stats
        }
    )


@router.get("/filter-panel", response_class=HTMLResponse)
async def filter_panel_fragment(
    request: Request
):
    """
    Serve the filter panel HTML fragment.

    This is a static component that provides the UI for filtering.
    """
    return templates.TemplateResponse(
        "fragments/filter_panel.html",
        {"request": request}
    )
