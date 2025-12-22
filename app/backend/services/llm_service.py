"""
LLM service for extracting structured vulnerability data from raw text.

Handles:
- Vulnerability data extraction (CVE ID, vendor, product, severity)
- Confidence scoring
- Format validation
- Low-confidence detection
"""

import logging
import re
from typing import Dict, Optional, List, Any
from datetime import datetime

from app.backend.services.ollama_client import OllamaClient, OllamaModelError

logger = logging.getLogger(__name__)


class ExtractionResult:
    """Result of LLM extraction with confidence score."""

    def __init__(
        self,
        cve_id: Optional[str],
        title: Optional[str],
        description: str,
        vendor: Optional[str],
        product: Optional[str],
        severity: Optional[str],
        cvss_score: Optional[float],
        cvss_vector: Optional[str],
        confidence_score: float,
        needs_review: bool,
        extraction_metadata: Dict[str, Any],
    ):
        self.cve_id = cve_id
        self.title = title
        self.description = description
        self.vendor = vendor
        self.product = product
        self.severity = severity
        self.cvss_score = cvss_score
        self.cvss_vector = cvss_vector
        self.confidence_score = confidence_score
        self.needs_review = needs_review
        self.extraction_metadata = extraction_metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "cve_id": self.cve_id,
            "title": self.title,
            "description": self.description,
            "vendor": self.vendor,
            "product": self.product,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "cvss_vector": self.cvss_vector,
            "confidence_score": self.confidence_score,
            "needs_review": self.needs_review,
            "extraction_metadata": self.extraction_metadata,
        }


class LLMService:
    """
    Service for extracting structured vulnerability data using LLM.

    Uses Ollama for local LLM inference with confidence scoring.
    """

    # CVE ID regex pattern
    CVE_PATTERN = re.compile(r'CVE-\d{4}-\d{4,}', re.IGNORECASE)

    # Valid severity levels
    VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE", "UNKNOWN"}

    # System prompt for extraction
    SYSTEM_PROMPT = """You are a cybersecurity data extraction assistant. Your task is to extract structured vulnerability information from raw text.

Extract the following fields:
- cve_id: CVE identifier (format: CVE-YYYY-NNNNN)
- title: Short vulnerability title
- description: Detailed description
- vendor: Affected vendor/organization
- product: Affected product name
- severity: One of CRITICAL, HIGH, MEDIUM, LOW, NONE, or UNKNOWN
- cvss_score: CVSS score if available (0.0-10.0)
- cvss_vector: CVSS vector string if available

Return ONLY a JSON object with these fields. Use null for missing values.
Be conservative - only extract information you are confident about."""

    def __init__(
        self,
        ollama_client: OllamaClient,
        model: str,
        temperature: float = 0.1,
        confidence_threshold: float = 0.8,
    ):
        """
        Initialize LLM service.

        Args:
            ollama_client: Configured Ollama client
            model: Model name to use for extraction
            temperature: Sampling temperature (lower = more deterministic)
            confidence_threshold: Below this score, mark as needs_review
        """
        self.ollama_client = ollama_client
        self.model = model
        self.temperature = temperature
        self.confidence_threshold = confidence_threshold

    async def extract_vulnerability(self, raw_text: str) -> ExtractionResult:
        """
        Extract structured vulnerability data from raw text.

        Args:
            raw_text: Raw vulnerability text from feed

        Returns:
            ExtractionResult with extracted data and confidence score

        Raises:
            OllamaModelError: If LLM generation fails
        """
        # Build extraction prompt
        prompt = f"""Extract vulnerability information from the following text:

{raw_text}

Return a JSON object with the extracted fields."""

        try:
            # Call LLM for extraction
            result = await self.ollama_client.generate_json(
                model=self.model,
                prompt=prompt,
                temperature=self.temperature,
                system_prompt=self.SYSTEM_PROMPT,
            )

            extracted_data = result["data"]
            llm_metadata = result["metadata"]

            # Validate and normalize extracted data
            validated = self._validate_extraction(extracted_data, raw_text)

            # Calculate confidence score
            confidence = self._calculate_confidence(validated, raw_text)

            # Determine if needs review
            needs_review = confidence < self.confidence_threshold

            return ExtractionResult(
                cve_id=validated.get("cve_id"),
                title=validated.get("title"),
                description=validated.get("description", raw_text[:500]),  # Fallback to raw text
                vendor=validated.get("vendor"),
                product=validated.get("product"),
                severity=validated.get("severity"),
                cvss_score=validated.get("cvss_score"),
                cvss_vector=validated.get("cvss_vector"),
                confidence_score=confidence,
                needs_review=needs_review,
                extraction_metadata={
                    "model": self.model,
                    "temperature": self.temperature,
                    "extraction_time": datetime.utcnow().isoformat(),
                    "llm_duration_ms": llm_metadata.get("total_duration_ms", 0),
                    "validation_issues": validated.get("_validation_issues", []),
                }
            )

        except OllamaModelError as e:
            logger.error(f"LLM extraction failed: {e}")
            # Return low-confidence result on error
            return self._create_fallback_result(raw_text, str(e))

    def _validate_extraction(self, data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """
        Validate and normalize extracted data.

        Args:
            data: Raw extracted data from LLM
            raw_text: Original raw text for fallback

        Returns:
            Validated and normalized data with validation issues
        """
        validated = {}
        issues = []

        # Validate CVE ID
        cve_id = data.get("cve_id")
        if cve_id:
            cve_id = str(cve_id).upper().strip()
            if self.CVE_PATTERN.fullmatch(cve_id):
                validated["cve_id"] = cve_id
            else:
                issues.append(f"Invalid CVE format: {cve_id}")
                # Try to extract from raw text
                match = self.CVE_PATTERN.search(raw_text)
                if match:
                    validated["cve_id"] = match.group(0).upper()
                    issues.append("CVE extracted from raw text instead")
        else:
            # Try to find CVE in raw text
            match = self.CVE_PATTERN.search(raw_text)
            if match:
                validated["cve_id"] = match.group(0).upper()
            else:
                issues.append("No CVE ID found")

        # Validate severity
        severity = data.get("severity")
        if severity:
            severity = str(severity).upper().strip()
            if severity in self.VALID_SEVERITIES:
                validated["severity"] = severity
            else:
                issues.append(f"Invalid severity: {severity}")
                validated["severity"] = "UNKNOWN"
        else:
            validated["severity"] = "UNKNOWN"

        # Validate CVSS score
        cvss_score = data.get("cvss_score")
        if cvss_score is not None:
            try:
                score = float(cvss_score)
                if 0.0 <= score <= 10.0:
                    validated["cvss_score"] = score
                else:
                    issues.append(f"CVSS score out of range: {score}")
            except (ValueError, TypeError):
                issues.append(f"Invalid CVSS score: {cvss_score}")

        # Simple string fields
        for field in ["title", "description", "vendor", "product", "cvss_vector"]:
            value = data.get(field)
            if value and str(value).strip():
                validated[field] = str(value).strip()

        # Ensure description exists
        if "description" not in validated or len(validated["description"]) < 10:
            validated["description"] = raw_text[:500]
            issues.append("Using raw text as description")

        validated["_validation_issues"] = issues
        return validated

    def _calculate_confidence(self, validated_data: Dict[str, Any], raw_text: str) -> float:
        """
        Calculate confidence score for extraction.

        Based on:
        - Presence of required fields
        - Format validation
        - Field quality

        Args:
            validated_data: Validated extraction data
            raw_text: Original raw text

        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 0.0

        # CVE ID (required, high weight)
        max_score += 30
        if validated_data.get("cve_id"):
            score += 30

        # Vendor/Product (important)
        max_score += 20
        if validated_data.get("vendor"):
            score += 10
        if validated_data.get("product"):
            score += 10

        # Severity (important)
        max_score += 15
        if validated_data.get("severity") and validated_data["severity"] != "UNKNOWN":
            score += 15

        # CVSS score (nice to have)
        max_score += 10
        if validated_data.get("cvss_score") is not None:
            score += 10

        # Description quality
        max_score += 15
        description = validated_data.get("description", "")
        if len(description) >= 50:
            score += 15
        elif len(description) >= 20:
            score += 10
        elif len(description) >= 10:
            score += 5

        # Title
        max_score += 10
        if validated_data.get("title"):
            score += 10

        # Deductions for validation issues
        issues = validated_data.get("_validation_issues", [])
        penalty = min(len(issues) * 5, 20)  # Max 20% penalty

        final_score = max(0.0, min(1.0, (score / max_score) - (penalty / 100)))

        return round(final_score, 3)

    def _create_fallback_result(self, raw_text: str, error_msg: str) -> ExtractionResult:
        """
        Create low-confidence fallback result when LLM fails.

        Args:
            raw_text: Original raw text
            error_msg: Error message

        Returns:
            ExtractionResult with extracted CVE if found, low confidence
        """
        # Try to extract CVE from raw text
        cve_match = self.CVE_PATTERN.search(raw_text)
        cve_id = cve_match.group(0).upper() if cve_match else None

        return ExtractionResult(
            cve_id=cve_id,
            title=None,
            description=raw_text[:500],
            vendor=None,
            product=None,
            severity="UNKNOWN",
            cvss_score=None,
            cvss_vector=None,
            confidence_score=0.1 if cve_id else 0.0,
            needs_review=True,
            extraction_metadata={
                "error": error_msg,
                "fallback": True,
                "extraction_time": datetime.utcnow().isoformat(),
            }
        )

    async def batch_extract(
        self,
        raw_texts: List[str],
        batch_size: int = 10
    ) -> List[ExtractionResult]:
        """
        Extract vulnerabilities from multiple raw texts.

        Args:
            raw_texts: List of raw text entries
            batch_size: Number to process at once (currently processes sequentially)

        Returns:
            List of extraction results
        """
        results = []

        for i, text in enumerate(raw_texts):
            logger.info(f"Processing entry {i+1}/{len(raw_texts)}")
            try:
                result = await self.extract_vulnerability(text)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process entry {i+1}: {e}")
                results.append(self._create_fallback_result(text, str(e)))

        return results
