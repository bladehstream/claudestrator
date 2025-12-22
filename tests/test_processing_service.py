"""
Tests for processing service.

Tests the core processing logic including deduplication, purging, and status tracking.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.backend.services.processing_service import ProcessingService, ProcessingStats
from app.backend.services.llm_service import ExtractionResult
from app.backend.models.database import (
    RawEntry, Vulnerability, LLMConfig, DataSource, ProcessingStatus
)


@pytest.fixture
def mock_db():
    """Mock async database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.get = AsyncMock()
    db.add = Mock()
    return db


@pytest.fixture
def sample_config():
    """Sample LLM configuration."""
    return LLMConfig(
        id=1,
        ollama_base_url="http://localhost:11434",
        selected_model="llama3",
        temperature=0.1,
        max_tokens=1000,
        confidence_threshold=0.8,
        processing_interval_minutes=30,
        batch_size=10,
    )


@pytest.fixture
def sample_raw_entry():
    """Sample raw entry."""
    return RawEntry(
        id=1,
        source_id=1,
        raw_payload="CVE-2024-1234: Critical vulnerability in Acme CMS",
        processing_status=ProcessingStatus.PENDING.value,
        processing_attempts=0,
        ingested_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_extraction():
    """Sample extraction result."""
    return ExtractionResult(
        cve_id="CVE-2024-1234",
        title="Critical vulnerability in Acme CMS",
        description="Authentication bypass in Acme CMS version 1.0",
        vendor="Acme",
        product="CMS",
        severity="CRITICAL",
        cvss_score=9.8,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        confidence_score=0.95,
        needs_review=False,
        extraction_metadata={"model": "llama3", "temperature": 0.1},
    )


@pytest.mark.asyncio
async def test_get_llm_config(mock_db, sample_config):
    """Test retrieving LLM configuration."""
    # Mock database query
    result = AsyncMock()
    result.scalar_one_or_none = Mock(return_value=sample_config)
    mock_db.execute = AsyncMock(return_value=result)

    service = ProcessingService(mock_db)
    config = await service.get_llm_config()

    assert config is not None
    assert config.selected_model == "llama3"
    assert config.batch_size == 10


@pytest.mark.asyncio
async def test_get_pending_entries(mock_db, sample_config):
    """Test getting pending entries."""
    # Mock config
    config_result = AsyncMock()
    config_result.scalar_one_or_none = Mock(return_value=sample_config)

    # Mock pending entries
    entries = [
        RawEntry(id=1, source_id=1, raw_payload="test1", processing_status=ProcessingStatus.PENDING.value, ingested_at=datetime.utcnow()),
        RawEntry(id=2, source_id=1, raw_payload="test2", processing_status=ProcessingStatus.PENDING.value, ingested_at=datetime.utcnow()),
    ]
    entries_result = AsyncMock()
    entries_result.scalars = Mock(return_value=Mock(all=Mock(return_value=entries)))

    mock_db.execute = AsyncMock(side_effect=[config_result, entries_result])

    service = ProcessingService(mock_db)
    pending = await service.get_pending_entries()

    assert len(pending) == 2
    assert pending[0].id == 1


@pytest.mark.asyncio
async def test_process_entry_new_vulnerability(mock_db, sample_raw_entry, sample_extraction):
    """Test processing entry creates new vulnerability."""
    # Mock no existing vulnerability
    mock_db.get = AsyncMock(return_value=None)

    # Mock LLM service
    llm_service = AsyncMock()
    llm_service.extract_vulnerability = AsyncMock(return_value=sample_extraction)

    config = LLMConfig(confidence_threshold=0.8)

    service = ProcessingService(mock_db)
    result = await service.process_entry(sample_raw_entry, llm_service, config)

    assert result is not None
    assert result.cve_id == "CVE-2024-1234"
    assert result.confidence_score == 0.95
    assert result.needs_review is False

    # Verify entry marked as completed
    assert sample_raw_entry.processing_status == ProcessingStatus.COMPLETED.value
    assert sample_raw_entry.processed_at is not None


@pytest.mark.asyncio
async def test_process_entry_update_higher_confidence(mock_db, sample_raw_entry, sample_extraction):
    """Test processing entry updates existing vulnerability with higher confidence."""
    # Mock existing vulnerability with lower confidence
    existing = Vulnerability(
        cve_id="CVE-2024-1234",
        description="Old description",
        confidence_score=0.7,
        needs_review=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mock_db.get = AsyncMock(return_value=existing)

    # Mock LLM service
    llm_service = AsyncMock()
    llm_service.extract_vulnerability = AsyncMock(return_value=sample_extraction)

    config = LLMConfig(confidence_threshold=0.8)

    service = ProcessingService(mock_db)
    result = await service.process_entry(sample_raw_entry, llm_service, config)

    assert result is not None
    assert result.cve_id == "CVE-2024-1234"
    assert result.confidence_score == 0.95  # Updated
    assert result.needs_review is False  # Updated


@pytest.mark.asyncio
async def test_process_entry_skip_lower_confidence(mock_db, sample_raw_entry, sample_extraction):
    """Test processing entry skips duplicate with lower confidence."""
    # Mock existing vulnerability with higher confidence
    existing = Vulnerability(
        cve_id="CVE-2024-1234",
        description="Existing description",
        confidence_score=0.98,  # Higher than sample (0.95)
        needs_review=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    mock_db.get = AsyncMock(return_value=existing)

    # Mock LLM service
    llm_service = AsyncMock()
    llm_service.extract_vulnerability = AsyncMock(return_value=sample_extraction)

    config = LLMConfig(confidence_threshold=0.8)

    service = ProcessingService(mock_db)
    result = await service.process_entry(sample_raw_entry, llm_service, config)

    # Should return None (skipped)
    assert result is None

    # Entry still marked as completed (no need to retry)
    assert sample_raw_entry.processing_status == ProcessingStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_process_entry_no_cve_id(mock_db, sample_raw_entry):
    """Test processing entry fails when no CVE ID extracted."""
    # Mock extraction with no CVE ID
    extraction = ExtractionResult(
        cve_id=None,
        title="Some vulnerability",
        description="No CVE ID found",
        vendor=None,
        product=None,
        severity="UNKNOWN",
        cvss_score=None,
        cvss_vector=None,
        confidence_score=0.3,
        needs_review=True,
        extraction_metadata={},
    )

    # Mock LLM service
    llm_service = AsyncMock()
    llm_service.extract_vulnerability = AsyncMock(return_value=extraction)

    config = LLMConfig(confidence_threshold=0.8)

    service = ProcessingService(mock_db)
    result = await service.process_entry(sample_raw_entry, llm_service, config)

    # Should return None (failed)
    assert result is None

    # Entry marked as failed
    assert sample_raw_entry.processing_status == ProcessingStatus.FAILED.value
    assert "No CVE ID" in sample_raw_entry.last_processing_error


@pytest.mark.asyncio
async def test_process_entry_exception_handling(mock_db, sample_raw_entry):
    """Test processing entry handles exceptions gracefully."""
    # Mock LLM service that raises exception
    llm_service = AsyncMock()
    llm_service.extract_vulnerability = AsyncMock(side_effect=Exception("LLM error"))

    config = LLMConfig(confidence_threshold=0.8)

    service = ProcessingService(mock_db)
    result = await service.process_entry(sample_raw_entry, llm_service, config)

    # Should return None (failed)
    assert result is None

    # Entry marked as failed with error
    assert sample_raw_entry.processing_status == ProcessingStatus.FAILED.value
    assert "LLM error" in sample_raw_entry.last_processing_error


@pytest.mark.asyncio
async def test_purge_old_entries(mock_db):
    """Test purging old processed entries."""
    # Mock delete result
    result = Mock()
    result.rowcount = 5
    mock_db.execute = AsyncMock(return_value=result)

    service = ProcessingService(mock_db)
    purged = await service.purge_old_entries(days=7)

    assert purged == 5
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_processing_status(mock_db):
    """Test getting processing status."""
    # Mock counts
    mock_db.scalar = AsyncMock(side_effect=[
        10,  # pending
        2,   # processing
        50,  # completed
        3,   # failed
        100, # total vulns
        15,  # needs review
    ])

    service = ProcessingService(mock_db)
    status = await service.get_processing_status()

    assert status["raw_entries"]["pending"] == 10
    assert status["raw_entries"]["processing"] == 2
    assert status["raw_entries"]["completed"] == 50
    assert status["raw_entries"]["failed"] == 3
    assert status["raw_entries"]["total"] == 65
    assert status["vulnerabilities"]["total"] == 100
    assert status["vulnerabilities"]["needs_review"] == 15
    assert status["vulnerabilities"]["approved"] == 85


def test_processing_stats():
    """Test processing stats tracking."""
    stats = ProcessingStats()

    assert stats.processed == 0
    assert stats.created == 0

    stats.processed = 10
    stats.created = 5
    stats.failed = 2

    stats.finish()

    assert stats.ended_at is not None
    assert stats.duration_seconds() > 0

    data = stats.to_dict()
    assert data["processed"] == 10
    assert data["created"] == 5
    assert data["failed"] == 2
    assert "started_at" in data
    assert "ended_at" in data
