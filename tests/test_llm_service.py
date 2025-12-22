"""
Tests for LLM extraction service.

Tests vulnerability extraction, confidence scoring, and validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.backend.services.llm_service import LLMService, ExtractionResult
from app.backend.services.ollama_client import OllamaClient


@pytest.fixture
def mock_ollama_client():
    """Create mock Ollama client."""
    client = MagicMock(spec=OllamaClient)
    return client


@pytest.fixture
def llm_service(mock_ollama_client):
    """Create LLM service with mock client."""
    return LLMService(
        ollama_client=mock_ollama_client,
        model="llama3",
        temperature=0.1,
        confidence_threshold=0.8
    )


@pytest.mark.asyncio
class TestLLMService:
    """Test suite for LLMService."""

    async def test_extract_vulnerability_success(self, llm_service, mock_ollama_client):
        """Test successful vulnerability extraction."""
        # Mock LLM response
        mock_ollama_client.generate_json = AsyncMock(return_value={
            "data": {
                "cve_id": "CVE-2024-1234",
                "title": "Critical Authentication Bypass",
                "description": "A critical vulnerability allows authentication bypass in the login module.",
                "vendor": "Acme Corp",
                "product": "Acme CMS",
                "severity": "CRITICAL",
                "cvss_score": 9.8,
                "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
            },
            "metadata": {
                "model": "llama3",
                "total_duration_ms": 1500
            }
        })

        raw_text = "CVE-2024-1234: Critical authentication bypass in Acme CMS"

        result = await llm_service.extract_vulnerability(raw_text)

        assert isinstance(result, ExtractionResult)
        assert result.cve_id == "CVE-2024-1234"
        assert result.vendor == "Acme Corp"
        assert result.product == "Acme CMS"
        assert result.severity == "CRITICAL"
        assert result.cvss_score == 9.8
        assert result.confidence_score > 0.8
        assert result.needs_review is False

    async def test_extract_vulnerability_with_validation_issues(self, llm_service, mock_ollama_client):
        """Test extraction with validation issues."""
        # Mock LLM response with invalid data
        mock_ollama_client.generate_json = AsyncMock(return_value={
            "data": {
                "cve_id": "INVALID-ID",
                "title": "Test",
                "description": "Short",
                "vendor": "Test Vendor",
                "product": None,
                "severity": "SUPER_HIGH",  # Invalid severity
                "cvss_score": 15.0,  # Out of range
                "cvss_vector": None
            },
            "metadata": {
                "model": "llama3",
                "total_duration_ms": 1200
            }
        })

        raw_text = "CVE-2024-5678: Test vulnerability"

        result = await llm_service.extract_vulnerability(raw_text)

        # Should extract CVE from raw text
        assert result.cve_id == "CVE-2024-5678"
        # Severity should be normalized to UNKNOWN
        assert result.severity == "UNKNOWN"
        # CVSS score should be None (out of range)
        assert result.cvss_score is None
        # Low confidence due to validation issues
        assert result.confidence_score < 0.8
        assert result.needs_review is True

    async def test_extract_vulnerability_no_cve(self, llm_service, mock_ollama_client):
        """Test extraction when no CVE ID is found."""
        mock_ollama_client.generate_json = AsyncMock(return_value={
            "data": {
                "cve_id": None,
                "title": "Unknown Vulnerability",
                "description": "A vulnerability was reported but no CVE assigned yet.",
                "vendor": "Unknown",
                "product": "Unknown",
                "severity": "MEDIUM",
                "cvss_score": None,
                "cvss_vector": None
            },
            "metadata": {
                "model": "llama3",
                "total_duration_ms": 1000
            }
        })

        raw_text = "Security issue reported in unknown product"

        result = await llm_service.extract_vulnerability(raw_text)

        assert result.cve_id is None
        # Low confidence without CVE
        assert result.confidence_score < 0.5
        assert result.needs_review is True

    async def test_confidence_calculation_high(self, llm_service):
        """Test confidence calculation with complete data."""
        validated_data = {
            "cve_id": "CVE-2024-1234",
            "vendor": "Vendor",
            "product": "Product",
            "severity": "CRITICAL",
            "cvss_score": 9.8,
            "description": "A detailed description of the vulnerability with sufficient length for analysis.",
            "title": "Critical Vulnerability",
            "_validation_issues": []
        }

        confidence = llm_service._calculate_confidence(validated_data, "raw text")

        assert confidence > 0.9
        assert confidence <= 1.0

    async def test_confidence_calculation_medium(self, llm_service):
        """Test confidence calculation with partial data."""
        validated_data = {
            "cve_id": "CVE-2024-1234",
            "vendor": "Vendor",
            "product": None,  # Missing
            "severity": "UNKNOWN",
            "cvss_score": None,
            "description": "Short description",
            "title": None,
            "_validation_issues": ["Missing product", "Unknown severity"]
        }

        confidence = llm_service._calculate_confidence(validated_data, "raw text")

        assert 0.3 < confidence < 0.7

    async def test_confidence_calculation_low(self, llm_service):
        """Test confidence calculation with minimal data."""
        validated_data = {
            "cve_id": None,
            "vendor": None,
            "product": None,
            "severity": "UNKNOWN",
            "cvss_score": None,
            "description": "Short",
            "title": None,
            "_validation_issues": ["No CVE", "No vendor", "No product"]
        }

        confidence = llm_service._calculate_confidence(validated_data, "raw text")

        assert confidence < 0.3

    async def test_fallback_result_creation(self, llm_service):
        """Test fallback result when LLM fails."""
        raw_text = "CVE-2024-9999: Some vulnerability description"
        error_msg = "LLM timeout"

        result = llm_service._create_fallback_result(raw_text, error_msg)

        assert isinstance(result, ExtractionResult)
        assert result.cve_id == "CVE-2024-9999"
        assert result.description == raw_text[:500]
        assert result.severity == "UNKNOWN"
        assert result.confidence_score == 0.1
        assert result.needs_review is True
        assert result.extraction_metadata["error"] == error_msg

    async def test_batch_extract(self, llm_service, mock_ollama_client):
        """Test batch extraction of multiple vulnerabilities."""
        mock_ollama_client.generate_json = AsyncMock(side_effect=[
            {
                "data": {
                    "cve_id": "CVE-2024-0001",
                    "title": "Vuln 1",
                    "description": "First vulnerability description",
                    "vendor": "Vendor1",
                    "product": "Product1",
                    "severity": "HIGH",
                    "cvss_score": 8.5,
                    "cvss_vector": None
                },
                "metadata": {"model": "llama3", "total_duration_ms": 1000}
            },
            {
                "data": {
                    "cve_id": "CVE-2024-0002",
                    "title": "Vuln 2",
                    "description": "Second vulnerability description",
                    "vendor": "Vendor2",
                    "product": "Product2",
                    "severity": "MEDIUM",
                    "cvss_score": 6.5,
                    "cvss_vector": None
                },
                "metadata": {"model": "llama3", "total_duration_ms": 1100}
            }
        ])

        raw_texts = [
            "CVE-2024-0001: First vulnerability",
            "CVE-2024-0002: Second vulnerability"
        ]

        results = await llm_service.batch_extract(raw_texts)

        assert len(results) == 2
        assert results[0].cve_id == "CVE-2024-0001"
        assert results[1].cve_id == "CVE-2024-0002"

    async def test_cve_pattern_matching(self, llm_service):
        """Test CVE pattern regex matching."""
        # Valid CVE patterns
        assert llm_service.CVE_PATTERN.search("CVE-2024-1234") is not None
        assert llm_service.CVE_PATTERN.search("CVE-2023-12345") is not None
        assert llm_service.CVE_PATTERN.search("cve-2022-99999") is not None

        # Invalid patterns
        assert llm_service.CVE_PATTERN.fullmatch("CVE-2024-123") is None  # Too short
        assert llm_service.CVE_PATTERN.search("INVALID-2024-1234") is None
        assert llm_service.CVE_PATTERN.search("CVE-999-1234") is None

    async def test_severity_validation(self, llm_service):
        """Test severity level validation."""
        assert "CRITICAL" in llm_service.VALID_SEVERITIES
        assert "HIGH" in llm_service.VALID_SEVERITIES
        assert "MEDIUM" in llm_service.VALID_SEVERITIES
        assert "LOW" in llm_service.VALID_SEVERITIES
        assert "UNKNOWN" in llm_service.VALID_SEVERITIES

        # Invalid severities
        assert "SUPER_HIGH" not in llm_service.VALID_SEVERITIES
        assert "MODERATE" not in llm_service.VALID_SEVERITIES
