"""
Tests for processing API endpoints.

Tests the REST API for processing management.
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime

from fastapi.testclient import TestClient
from app.main import app
from app.backend.services.processing_service import ProcessingStats


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_scheduler():
    """Mock scheduler."""
    with patch('app.backend.api.processing.get_scheduler') as mock:
        scheduler = Mock()
        mock.return_value = scheduler
        yield scheduler


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    with patch('app.backend.api.processing.get_db') as mock:
        db = AsyncMock()
        mock.return_value = db
        yield db


def test_trigger_processing_success(client, mock_scheduler):
    """Test manual processing trigger endpoint."""
    # Mock stats
    stats = ProcessingStats()
    stats.processed = 10
    stats.created = 5
    stats.updated = 2
    stats.failed = 1
    stats.skipped = 2
    stats.duplicates = 4
    stats.purged = 3
    stats.finish()

    mock_scheduler.trigger_now = AsyncMock(return_value=stats)

    response = client.post("/admin/processing/trigger")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Processing cycle completed successfully"
    assert data["stats"]["processed"] == 10
    assert data["stats"]["created"] == 5


def test_trigger_processing_error(client, mock_scheduler):
    """Test processing trigger with error."""
    mock_scheduler.trigger_now = AsyncMock(side_effect=Exception("Processing failed"))

    response = client.post("/admin/processing/trigger")

    assert response.status_code == 500
    assert "Processing failed" in response.json()["detail"]


def test_get_processing_status(client):
    """Test getting processing status."""
    with patch('app.backend.api.processing.ProcessingService') as mock_service_class:
        service = AsyncMock()
        mock_service_class.return_value = service

        service.get_processing_status = AsyncMock(return_value={
            "raw_entries": {
                "pending": 10,
                "processing": 2,
                "completed": 50,
                "failed": 3,
                "total": 65,
            },
            "vulnerabilities": {
                "total": 100,
                "needs_review": 15,
                "approved": 85,
            },
        })

        response = client.get("/admin/processing/status")

        assert response.status_code == 200
        data = response.json()
        assert data["raw_entries"]["pending"] == 10
        assert data["vulnerabilities"]["total"] == 100


def test_get_scheduler_status_running(client, mock_scheduler):
    """Test getting scheduler status when running."""
    stats = ProcessingStats()
    stats.processed = 5
    stats.finish()

    mock_scheduler.get_status = Mock(return_value={
        "is_running": True,
        "last_run": datetime.utcnow().isoformat(),
        "last_stats": stats.to_dict(),
    })

    response = client.get("/admin/processing/scheduler")

    assert response.status_code == 200
    data = response.json()
    assert data["is_running"] is True
    assert data["last_run"] is not None
    assert data["last_stats"]["processed"] == 5


def test_get_scheduler_status_not_running(client, mock_scheduler):
    """Test getting scheduler status when not running."""
    mock_scheduler.get_status = Mock(return_value={
        "is_running": False,
        "last_run": None,
        "last_stats": None,
    })

    response = client.get("/admin/processing/scheduler")

    assert response.status_code == 200
    data = response.json()
    assert data["is_running"] is False
    assert data["last_run"] is None


def test_start_scheduler_success(client, mock_scheduler):
    """Test starting scheduler."""
    mock_scheduler.is_running = False
    mock_scheduler.start = Mock()

    response = client.post("/admin/processing/scheduler/start")

    assert response.status_code == 200
    assert "started successfully" in response.json()["message"]
    mock_scheduler.start.assert_called_once()


def test_start_scheduler_already_running(client, mock_scheduler):
    """Test starting scheduler when already running."""
    mock_scheduler.is_running = True

    response = client.post("/admin/processing/scheduler/start")

    assert response.status_code == 400
    assert "already running" in response.json()["detail"]


def test_stop_scheduler_success(client, mock_scheduler):
    """Test stopping scheduler."""
    mock_scheduler.is_running = True
    mock_scheduler.stop = AsyncMock()

    response = client.post("/admin/processing/scheduler/stop")

    assert response.status_code == 200
    assert "stopped successfully" in response.json()["message"]
    mock_scheduler.stop.assert_called_once()


def test_stop_scheduler_not_running(client, mock_scheduler):
    """Test stopping scheduler when not running."""
    mock_scheduler.is_running = False

    response = client.post("/admin/processing/scheduler/stop")

    assert response.status_code == 400
    assert "not running" in response.json()["detail"]


def test_purge_old_entries_default(client):
    """Test purging old entries with default days."""
    with patch('app.backend.api.processing.ProcessingService') as mock_service_class:
        service = AsyncMock()
        mock_service_class.return_value = service
        service.purge_old_entries = AsyncMock(return_value=15)

        response = client.post("/admin/processing/purge")

        assert response.status_code == 200
        data = response.json()
        assert data["purged_count"] == 15
        assert "7 days" in data["message"]


def test_purge_old_entries_custom_days(client):
    """Test purging old entries with custom days."""
    with patch('app.backend.api.processing.ProcessingService') as mock_service_class:
        service = AsyncMock()
        mock_service_class.return_value = service
        service.purge_old_entries = AsyncMock(return_value=25)

        response = client.post("/admin/processing/purge", json={"days": 14})

        assert response.status_code == 200
        data = response.json()
        assert data["purged_count"] == 25
        assert "14 days" in data["message"]
        service.purge_old_entries.assert_called_once_with(days=14)


def test_purge_old_entries_validation(client):
    """Test purge validation."""
    # Test days too low
    response = client.post("/admin/processing/purge", json={"days": 0})
    assert response.status_code == 422

    # Test days too high
    response = client.post("/admin/processing/purge", json={"days": 100})
    assert response.status_code == 422


def test_purge_old_entries_error(client):
    """Test purge with error."""
    with patch('app.backend.api.processing.ProcessingService') as mock_service_class:
        service = AsyncMock()
        mock_service_class.return_value = service
        service.purge_old_entries = AsyncMock(side_effect=Exception("Database error"))

        response = client.post("/admin/processing/purge")

        assert response.status_code == 500
        assert "Purge failed" in response.json()["detail"]
