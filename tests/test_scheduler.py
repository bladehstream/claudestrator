"""
Tests for background scheduler.

Tests scheduler lifecycle, manual triggering, and interval management.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime

from app.backend.services.scheduler import ProcessingScheduler, get_scheduler
from app.backend.services.processing_service import ProcessingStats


@pytest.mark.asyncio
async def test_scheduler_initialization():
    """Test scheduler initializes correctly."""
    scheduler = ProcessingScheduler()

    assert scheduler.is_running is False
    assert scheduler.task is None
    assert scheduler.last_run is None
    assert scheduler.last_stats is None


@pytest.mark.asyncio
async def test_get_interval_minutes():
    """Test getting interval from config."""
    scheduler = ProcessingScheduler()

    with patch('app.backend.services.scheduler.AsyncSessionLocal') as mock_session:
        # Mock database session
        db = AsyncMock()
        mock_session.return_value.__aenter__ = AsyncMock(return_value=db)
        mock_session.return_value.__aexit__ = AsyncMock()

        # Mock config
        from app.backend.models.database import LLMConfig
        config = LLMConfig(processing_interval_minutes=15)

        result = AsyncMock()
        result.scalar_one_or_none = Mock(return_value=config)
        db.execute = AsyncMock(return_value=result)

        interval = await scheduler.get_interval_minutes()
        assert interval == 15


@pytest.mark.asyncio
async def test_get_interval_default():
    """Test default interval when no config."""
    scheduler = ProcessingScheduler()

    with patch('app.backend.services.scheduler.AsyncSessionLocal') as mock_session:
        db = AsyncMock()
        mock_session.return_value.__aenter__ = AsyncMock(return_value=db)
        mock_session.return_value.__aexit__ = AsyncMock()

        # Mock no config
        result = AsyncMock()
        result.scalar_one_or_none = Mock(return_value=None)
        db.execute = AsyncMock(return_value=result)

        interval = await scheduler.get_interval_minutes()
        assert interval == 30  # Default


@pytest.mark.asyncio
async def test_run_processing_cycle():
    """Test single processing cycle execution."""
    scheduler = ProcessingScheduler()

    with patch('app.backend.services.scheduler.AsyncSessionLocal') as mock_session:
        db = AsyncMock()
        mock_session.return_value.__aenter__ = AsyncMock(return_value=db)
        mock_session.return_value.__aexit__ = AsyncMock()

        # Mock processing service
        with patch('app.backend.services.scheduler.ProcessingService') as mock_service_class:
            service = AsyncMock()
            mock_service_class.return_value = service

            # Mock stats
            stats = ProcessingStats()
            stats.processed = 5
            stats.created = 3
            service.process_batch = AsyncMock(return_value=stats)
            service.purge_old_entries = AsyncMock(return_value=2)

            result = await scheduler.run_processing_cycle()

            assert result.processed == 5
            assert result.created == 3
            assert result.purged == 2
            assert scheduler.last_run is not None
            assert scheduler.last_stats is not None


@pytest.mark.asyncio
async def test_trigger_now():
    """Test manual trigger."""
    scheduler = ProcessingScheduler()

    with patch.object(scheduler, 'run_processing_cycle') as mock_run:
        stats = ProcessingStats()
        stats.processed = 10
        mock_run.return_value = stats

        result = await scheduler.trigger_now()

        assert result.processed == 10
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_start_stop():
    """Test starting and stopping scheduler."""
    scheduler = ProcessingScheduler()

    # Mock the run loop to not actually run
    with patch.object(scheduler, '_run_loop') as mock_loop:
        mock_loop.return_value = asyncio.sleep(0)

        # Start
        scheduler.start()
        assert scheduler.is_running is True
        assert scheduler.task is not None

        # Allow task to be created
        await asyncio.sleep(0.01)

        # Stop
        await scheduler.stop()
        assert scheduler.is_running is False
        assert scheduler.task is None


@pytest.mark.asyncio
async def test_scheduler_start_already_running():
    """Test starting scheduler when already running."""
    scheduler = ProcessingScheduler()
    scheduler.is_running = True

    # Should not create new task
    scheduler.start()
    # No assertion needed - just checking it doesn't crash


@pytest.mark.asyncio
async def test_scheduler_stop_not_running():
    """Test stopping scheduler when not running."""
    scheduler = ProcessingScheduler()
    scheduler.is_running = False

    # Should not crash
    await scheduler.stop()


@pytest.mark.asyncio
async def test_get_status():
    """Test getting scheduler status."""
    scheduler = ProcessingScheduler()

    # Initial status
    status = scheduler.get_status()
    assert status["is_running"] is False
    assert status["last_run"] is None
    assert status["last_stats"] is None

    # After run
    scheduler.is_running = True
    scheduler.last_run = datetime.utcnow()
    stats = ProcessingStats()
    stats.processed = 5
    scheduler.last_stats = stats

    status = scheduler.get_status()
    assert status["is_running"] is True
    assert status["last_run"] is not None
    assert status["last_stats"]["processed"] == 5


def test_get_scheduler_singleton():
    """Test global scheduler singleton."""
    scheduler1 = get_scheduler()
    scheduler2 = get_scheduler()

    # Should be same instance
    assert scheduler1 is scheduler2
