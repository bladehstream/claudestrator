"""
Unit tests for EPSS enrichment service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import httpx

from app.backend.services.epss_enrichment import (
    EPSSEnrichmentService,
    run_epss_enrichment,
    EPSS_API_BASE_URL
)
from app.database.models import Vulnerability


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_vulnerability():
    """Mock vulnerability object."""
    vuln = MagicMock(spec=Vulnerability)
    vuln.cve_id = "CVE-2024-1234"
    vuln.epss_score = None
    vuln.epss_percentile = None
    vuln.enriched_at = None
    vuln.created_at = datetime.utcnow()
    return vuln


@pytest.fixture
def epss_api_response():
    """Mock EPSS API successful response."""
    return {
        "status": "OK",
        "data": [
            {
                "cve": "CVE-2024-1234",
                "epss": "0.12345",
                "percentile": "0.89012"
            }
        ]
    }


@pytest.mark.asyncio
async def test_fetch_epss_score_success(mock_db, epss_api_response):
    """Test successful EPSS score fetch."""
    service = EPSSEnrichmentService(mock_db)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = epss_api_response
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        async with service:
            result = await service._fetch_epss_score("CVE-2024-1234")

        assert result is not None
        assert result["epss"] == 0.12345
        assert result["percentile"] == 0.89012


@pytest.mark.asyncio
async def test_fetch_epss_score_not_found(mock_db):
    """Test EPSS score fetch for CVE not in database (404)."""
    service = EPSSEnrichmentService(mock_db)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        async with service:
            result = await service._fetch_epss_score("CVE-2024-9999")

        assert result is None


@pytest.mark.asyncio
async def test_fetch_epss_score_rate_limited(mock_db, epss_api_response):
    """Test EPSS score fetch with rate limiting (429)."""
    service = EPSSEnrichmentService(mock_db)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()

        # First call returns 429, second call succeeds
        mock_response_429 = AsyncMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}

        mock_response_200 = AsyncMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = epss_api_response

        mock_client.get.side_effect = [mock_response_429, mock_response_200]
        mock_client_class.return_value = mock_client

        async with service:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await service._fetch_epss_score("CVE-2024-1234")

        assert result is not None
        assert result["epss"] == 0.12345


@pytest.mark.asyncio
async def test_fetch_epss_score_http_error(mock_db):
    """Test EPSS score fetch with HTTP error."""
    service = EPSSEnrichmentService(mock_db)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        async with service:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await service._fetch_epss_score("CVE-2024-1234")

        assert result is None


@pytest.mark.asyncio
async def test_enrich_vulnerability_success(mock_db, mock_vulnerability, epss_api_response):
    """Test successful vulnerability enrichment."""
    service = EPSSEnrichmentService(mock_db)

    with patch.object(service, "_fetch_epss_score", return_value={
        "epss": 0.12345,
        "percentile": 0.89012
    }):
        async with service:
            result = await service.enrich_vulnerability(mock_vulnerability)

        assert result is True
        assert mock_vulnerability.epss_score == 0.12345
        assert mock_vulnerability.epss_percentile == 0.89012
        assert mock_vulnerability.enriched_at is not None
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_enrich_vulnerability_not_found(mock_db, mock_vulnerability):
    """Test enrichment when CVE not found in EPSS database."""
    service = EPSSEnrichmentService(mock_db)

    with patch.object(service, "_fetch_epss_score", return_value=None):
        async with service:
            result = await service.enrich_vulnerability(mock_vulnerability)

        assert result is False
        assert mock_vulnerability.epss_score is None
        mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_enrich_vulnerability_error(mock_db, mock_vulnerability):
    """Test enrichment with error handling."""
    service = EPSSEnrichmentService(mock_db)

    with patch.object(service, "_fetch_epss_score", side_effect=Exception("API error")):
        async with service:
            result = await service.enrich_vulnerability(mock_vulnerability)

        assert result is False
        mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_vulnerabilities_needing_enrichment(mock_db):
    """Test query for vulnerabilities needing enrichment."""
    service = EPSSEnrichmentService(mock_db)

    # Mock query result
    mock_result = AsyncMock()
    mock_scalars = MagicMock()
    mock_vulnerabilities = [
        MagicMock(cve_id="CVE-2024-1111", epss_score=None),
        MagicMock(cve_id="CVE-2024-2222", epss_score=None),
    ]
    mock_scalars.all.return_value = mock_vulnerabilities
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    async with service:
        vulnerabilities = await service.get_vulnerabilities_needing_enrichment(limit=10)

    assert len(vulnerabilities) == 2
    assert vulnerabilities[0].cve_id == "CVE-2024-1111"
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_enrich_batch(mock_db):
    """Test batch enrichment of vulnerabilities."""
    service = EPSSEnrichmentService(mock_db)

    # Mock vulnerabilities needing enrichment
    mock_vulns = [
        MagicMock(cve_id="CVE-2024-1111", epss_score=None),
        MagicMock(cve_id="CVE-2024-2222", epss_score=None),
    ]

    with patch.object(service, "get_vulnerabilities_needing_enrichment", return_value=mock_vulns):
        with patch.object(service, "enrich_vulnerability", side_effect=[True, False]):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with service:
                    stats = await service.enrich_batch(limit=10)

    assert stats["processed"] == 2
    assert stats["enriched"] == 1
    assert stats["not_found"] == 1


@pytest.mark.asyncio
async def test_enrich_batch_preserves_metadata(mock_db, mock_vulnerability):
    """Test that enrichment only updates EPSS fields."""
    # Set existing metadata
    mock_vulnerability.cvss_score = 7.5
    mock_vulnerability.confidence_score = 0.95
    mock_vulnerability.severity = "HIGH"

    service = EPSSEnrichmentService(mock_db)

    with patch.object(service, "_fetch_epss_score", return_value={
        "epss": 0.12345,
        "percentile": 0.89012
    }):
        async with service:
            result = await service.enrich_vulnerability(mock_vulnerability)

    # Verify EPSS fields updated
    assert mock_vulnerability.epss_score == 0.12345
    assert mock_vulnerability.epss_percentile == 0.89012

    # Verify other fields unchanged
    assert mock_vulnerability.cvss_score == 7.5
    assert mock_vulnerability.confidence_score == 0.95
    assert mock_vulnerability.severity == "HIGH"


@pytest.mark.asyncio
async def test_run_epss_enrichment_convenience_function(mock_db):
    """Test convenience function for running enrichment."""
    with patch("app.backend.services.epss_enrichment.EPSSEnrichmentService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.enrich_batch.return_value = {
            "processed": 5,
            "enriched": 4,
            "not_found": 1,
            "errors": 0
        }
        mock_service_class.return_value.__aenter__.return_value = mock_service

        stats = await run_epss_enrichment(mock_db, limit=10)

        assert stats["processed"] == 5
        assert stats["enriched"] == 4
