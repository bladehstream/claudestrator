"""
Unit tests for EPSS scheduler.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.backend.services.epss_scheduler import (
    EPSSScheduler,
    get_epss_scheduler,
    start_epss_scheduler,
    stop_epss_scheduler
)


@pytest.mark.asyncio
async def test_scheduler_initialization():
    """Test scheduler initialization."""
    scheduler = EPSSScheduler(
        interval_hours=12,
        batch_size=50,
        max_age_days=14
    )

    assert scheduler.interval_hours == 12
    assert scheduler.batch_size == 50
    assert scheduler.max_age_days == 14
    assert scheduler.is_running is False
    assert scheduler.last_run is None


@pytest.mark.asyncio
async def test_scheduler_interval_constraints():
    """Test scheduler interval constraints (1-168 hours)."""
    # Too low
    scheduler = EPSSScheduler(interval_hours=0)
    assert scheduler.interval_hours == 1

    # Too high
    scheduler = EPSSScheduler(interval_hours=200)
    assert scheduler.interval_hours == 168

    # Valid
    scheduler = EPSSScheduler(interval_hours=48)
    assert scheduler.interval_hours == 48


@pytest.mark.asyncio
async def test_scheduler_batch_size_constraints():
    """Test scheduler batch size constraints (1-1000)."""
    # Too low
    scheduler = EPSSScheduler(batch_size=0)
    assert scheduler.batch_size == 1

    # Too high
    scheduler = EPSSScheduler(batch_size=5000)
    assert scheduler.batch_size == 1000

    # Valid
    scheduler = EPSSScheduler(batch_size=200)
    assert scheduler.batch_size == 200


@pytest.mark.asyncio
async def test_run_enrichment_cycle_success():
    """Test successful enrichment cycle."""
    scheduler = EPSSScheduler(interval_hours=1, batch_size=10)

    with patch("app.backend.services.epss_scheduler.run_epss_enrichment") as mock_run:
        mock_run.return_value = {
            "processed": 10,
            "enriched": 8,
            "not_found": 2,
            "errors": 0
        }

        stats = await scheduler.run_enrichment_cycle()

        assert stats["enriched"] == 8
        assert stats["not_found"] == 2
        assert scheduler.last_run is not None
        assert scheduler.last_stats == stats


@pytest.mark.asyncio
async def test_run_enrichment_cycle_error():
    """Test enrichment cycle with error."""
    scheduler = EPSSScheduler(interval_hours=1, batch_size=10)

    with patch("app.backend.services.epss_scheduler.run_epss_enrichment") as mock_run:
        mock_run.side_effect = Exception("Database error")

        stats = await scheduler.run_enrichment_cycle()

        assert stats["errors"] == 1
        assert "error_message" in stats
        assert scheduler.last_stats == stats


@pytest.mark.asyncio
async def test_scheduler_start():
    """Test starting the scheduler."""
    scheduler = EPSSScheduler(interval_hours=1, batch_size=10)

    with patch.object(scheduler, "_run_loop", new_callable=AsyncMock):
        scheduler.start()

        assert scheduler.is_running is True
        assert scheduler.task is not None


@pytest.mark.asyncio
async def test_scheduler_start_already_running():
    """Test starting scheduler when already running."""
    scheduler = EPSSScheduler(interval_hours=1, batch_size=10)
    scheduler.is_running = True

    scheduler.start()

    # Should not create new task
    assert scheduler.task is None


@pytest.mark.asyncio
async def test_scheduler_stop():
    """Test stopping the scheduler."""
    scheduler = EPSSScheduler(interval_hours=1, batch_size=10)

    # Start scheduler
    with patch.object(scheduler, "_run_loop", new_callable=AsyncMock):
        scheduler.start()

    # Stop scheduler
    await scheduler.stop()

    assert scheduler.is_running is False
    assert scheduler.task is None


@pytest.mark.asyncio
async def test_scheduler_stop_not_running():
    """Test stopping scheduler when not running."""
    scheduler = EPSSScheduler(interval_hours=1, batch_size=10)

    await scheduler.stop()

    # Should handle gracefully
    assert scheduler.is_running is False


@pytest.mark.asyncio
async def test_scheduler_trigger_now():
    """Test manual trigger of scheduler."""
    scheduler = EPSSScheduler(interval_hours=1, batch_size=10)

    with patch.object(scheduler, "run_enrichment_cycle") as mock_run:
        mock_run.return_value = {
            "processed": 5,
            "enriched": 4,
            "not_found": 1,
            "errors": 0
        }

        stats = await scheduler.trigger_now()

        assert stats["enriched"] == 4
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_get_status():
    """Test getting scheduler status."""
    scheduler = EPSSScheduler(interval_hours=24, batch_size=100, max_age_days=7)
    scheduler.is_running = True
    scheduler.last_run = datetime.utcnow()
    scheduler.last_stats = {"processed": 10, "enriched": 8}

    status = scheduler.get_status()

    assert status["is_running"] is True
    assert status["interval_hours"] == 24
    assert status["batch_size"] == 100
    assert status["max_age_days"] == 7
    assert status["last_run"] is not None
    assert status["last_stats"]["enriched"] == 8


@pytest.mark.asyncio
async def test_get_epss_scheduler_singleton():
    """Test global scheduler singleton."""
    # Reset global
    import app.backend.services.epss_scheduler as scheduler_module
    scheduler_module._epss_scheduler = None

    scheduler1 = get_epss_scheduler()
    scheduler2 = get_epss_scheduler()

    # Should return same instance
    assert scheduler1 is scheduler2


@pytest.mark.asyncio
async def test_start_epss_scheduler_function():
    """Test start_epss_scheduler convenience function."""
    with patch("app.backend.services.epss_scheduler.get_epss_scheduler") as mock_get:
        mock_scheduler = AsyncMock()
        mock_get.return_value = mock_scheduler

        await start_epss_scheduler()

        mock_scheduler.start.assert_called_once()


@pytest.mark.asyncio
async def test_stop_epss_scheduler_function():
    """Test stop_epss_scheduler convenience function."""
    with patch("app.backend.services.epss_scheduler.get_epss_scheduler") as mock_get:
        mock_scheduler = AsyncMock()
        mock_get.return_value = mock_scheduler

        await stop_epss_scheduler()

        mock_scheduler.stop.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_run_loop_cycle():
    """Test scheduler run loop executes cycles."""
    scheduler = EPSSScheduler(interval_hours=1, batch_size=10)

    with patch.object(scheduler, "run_enrichment_cycle") as mock_cycle:
        mock_cycle.return_value = {"processed": 1, "enriched": 1, "not_found": 0, "errors": 0}

        # Start scheduler
        scheduler.start()

        # Wait a bit then stop
        import asyncio
        await asyncio.sleep(0.1)
        await scheduler.stop()

        # Should have run at least one cycle
        assert mock_cycle.called
