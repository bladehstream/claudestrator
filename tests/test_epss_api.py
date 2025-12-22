"""
Unit tests for EPSS API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


client = TestClient(app)


@pytest.mark.asyncio
async def test_trigger_epss_enrichment_success():
    """Test POST /admin/epss/trigger endpoint."""
    with patch("app.backend.api.epss.run_epss_enrichment") as mock_run:
        mock_run.return_value = {
            "processed": 10,
            "enriched": 8,
            "not_found": 2,
            "errors": 0
        }

        response = client.post("/admin/epss/trigger", json={
            "limit": 10,
            "max_age_days": 7
        })

        assert response.status_code == 200
        data = response.json()
        assert data["enriched"] == 8
        assert data["not_found"] == 2
        assert "Enrichment complete" in data["message"]


@pytest.mark.asyncio
async def test_trigger_epss_enrichment_validation():
    """Test input validation for trigger endpoint."""
    # Invalid limit (too high)
    response = client.post("/admin/epss/trigger", json={
        "limit": 5000,
        "max_age_days": 7
    })
    assert response.status_code == 422

    # Invalid max_age_days (too low)
    response = client.post("/admin/epss/trigger", json={
        "limit": 10,
        "max_age_days": 0
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_trigger_epss_enrichment_error():
    """Test error handling in trigger endpoint."""
    with patch("app.backend.api.epss.run_epss_enrichment") as mock_run:
        mock_run.side_effect = Exception("Database connection failed")

        response = client.post("/admin/epss/trigger", json={
            "limit": 10,
            "max_age_days": 7
        })

        assert response.status_code == 500
        assert "EPSS enrichment failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_epss_scheduler_status():
    """Test GET /admin/epss/status endpoint."""
    with patch("app.backend.api.epss.get_epss_scheduler") as mock_get:
        mock_scheduler = AsyncMock()
        mock_scheduler.get_status.return_value = {
            "is_running": True,
            "interval_hours": 24,
            "batch_size": 100,
            "max_age_days": 7,
            "last_run": "2024-01-01T12:00:00",
            "last_stats": {"processed": 50, "enriched": 45}
        }
        mock_get.return_value = mock_scheduler

        response = client.get("/admin/epss/status")

        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is True
        assert data["interval_hours"] == 24
        assert data["last_stats"]["enriched"] == 45


@pytest.mark.asyncio
async def test_start_epss_scheduler_endpoint():
    """Test POST /admin/epss/scheduler/start endpoint."""
    with patch("app.backend.api.epss.get_epss_scheduler") as mock_get:
        mock_scheduler = AsyncMock()
        mock_scheduler.is_running = False
        mock_scheduler.interval_hours = 24
        mock_get.return_value = mock_scheduler

        response = client.post("/admin/epss/scheduler/start")

        assert response.status_code == 200
        assert "EPSS scheduler started" in response.json()["message"]
        mock_scheduler.start.assert_called_once()


@pytest.mark.asyncio
async def test_start_epss_scheduler_already_running():
    """Test starting scheduler when already running."""
    with patch("app.backend.api.epss.get_epss_scheduler") as mock_get:
        mock_scheduler = AsyncMock()
        mock_scheduler.is_running = True
        mock_get.return_value = mock_scheduler

        response = client.post("/admin/epss/scheduler/start")

        assert response.status_code == 400
        assert "already running" in response.json()["detail"]


@pytest.mark.asyncio
async def test_stop_epss_scheduler_endpoint():
    """Test POST /admin/epss/scheduler/stop endpoint."""
    with patch("app.backend.api.epss.get_epss_scheduler") as mock_get:
        mock_scheduler = AsyncMock()
        mock_scheduler.is_running = True
        mock_get.return_value = mock_scheduler

        response = client.post("/admin/epss/scheduler/stop")

        assert response.status_code == 200
        assert "EPSS scheduler stopped" in response.json()["message"]
        mock_scheduler.stop.assert_called_once()


@pytest.mark.asyncio
async def test_stop_epss_scheduler_not_running():
    """Test stopping scheduler when not running."""
    with patch("app.backend.api.epss.get_epss_scheduler") as mock_get:
        mock_scheduler = AsyncMock()
        mock_scheduler.is_running = False
        mock_get.return_value = mock_scheduler

        response = client.post("/admin/epss/scheduler/stop")

        assert response.status_code == 400
        assert "not running" in response.json()["detail"]


@pytest.mark.asyncio
async def test_trigger_epss_scheduler_now():
    """Test POST /admin/epss/scheduler/trigger endpoint."""
    with patch("app.backend.api.epss.get_epss_scheduler") as mock_get:
        mock_scheduler = AsyncMock()
        mock_scheduler.trigger_now.return_value = {
            "processed": 25,
            "enriched": 20,
            "not_found": 5,
            "errors": 0
        }
        mock_get.return_value = mock_scheduler

        response = client.post("/admin/epss/scheduler/trigger")

        assert response.status_code == 200
        data = response.json()
        assert data["enriched"] == 20
        assert "Scheduler triggered" in data["message"]


@pytest.mark.asyncio
async def test_trigger_epss_scheduler_error():
    """Test scheduler trigger with error."""
    with patch("app.backend.api.epss.get_epss_scheduler") as mock_get:
        mock_scheduler = AsyncMock()
        mock_scheduler.trigger_now.side_effect = Exception("Scheduler error")
        mock_get.return_value = mock_scheduler

        response = client.post("/admin/epss/scheduler/trigger")

        assert response.status_code == 500
        assert "Scheduler trigger failed" in response.json()["detail"]
