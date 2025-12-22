"""
Multi-provider LLM service with fallback logic.

Handles:
- Multiple LLM providers (Ollama, Claude, Gemini)
- Automatic fallback if primary provider fails
- Vulnerability data extraction with confidence scoring
- Format validation with fallback extraction
"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

from app.backend.services.llm_providers import (
    LLMProvider,
    LLMProviderFactory,
    LLMConnectionError,
    LLMGenerationError,
)
from app.backend.services.llm_service import ExtractionResult, LLMService

logger = logging.getLogger(__name__)


class MultiProviderLLMService:
    """
    Multi-provider LLM service with automatic fallback.

    Uses a primary LLM provider and falls back to alternatives if the primary fails.
    """

    def __init__(
        self,
        primary_provider: LLMProvider,
        fallback_providers: Optional[List[LLMProvider]] = None,
        model: str = "auto",
        temperature: float = 0.1,
        confidence_threshold: float = 0.8,
        max_retries: int = 3,
    ):
        """
        Initialize multi-provider LLM service.

        Args:
            primary_provider: Primary LLM provider instance
            fallback_providers: List of fallback providers (tried in order)
            model: Model name/ID ('auto' = auto-select from provider)
            temperature: Sampling temperature
            confidence_threshold: Confidence score threshold for review
            max_retries: Maximum retry attempts across all providers
        """
        self.primary_provider = primary_provider
        self.fallback_providers = fallback_providers or []
        self.model = model
        self.temperature = temperature
        self.confidence_threshold = confidence_threshold
        self.max_retries = max_retries

        # Use single-provider service as base for extraction logic
        self.extractor = LLMService(
            # Create a dummy Ollama client for compatibility
            # The actual generation will be overridden
            ollama_client=None,
            model=model,
            temperature=temperature,
            confidence_threshold=confidence_threshold,
        )

    async def extract_vulnerability(self, raw_text: str) -> ExtractionResult:
        """
        Extract structured vulnerability data from raw text.

        Attempts primary provider first, then falls back to alternatives.

        Args:
            raw_text: Raw vulnerability text from feed

        Returns:
            ExtractionResult with extracted data and confidence score
        """
        providers_to_try = [self.primary_provider] + self.fallback_providers
        last_error = None

        for attempt, provider in enumerate(providers_to_try):
            if attempt >= self.max_retries:
                logger.warning(f"Max retries ({self.max_retries}) reached")
                break

            try:
                logger.info(
                    f"Attempt {attempt + 1}/{len(providers_to_try)}: "
                    f"Extracting with {provider.provider_name}"
                )

                # Generate JSON from provider
                result = await provider.generate_json(
                    model=self.model,
                    prompt=self._build_extraction_prompt(raw_text),
                    system_prompt=LLMService.SYSTEM_PROMPT,
                    temperature=self.temperature,
                )

                extracted_data = result["data"]
                provider_metadata = result["metadata"]

                # Validate and normalize extracted data
                validated = self.extractor._validate_extraction(extracted_data, raw_text)

                # Calculate confidence score
                confidence = self.extractor._calculate_confidence(validated, raw_text)

                # Determine if needs review
                needs_review = confidence < self.confidence_threshold

                return ExtractionResult(
                    cve_id=validated.get("cve_id"),
                    title=validated.get("title"),
                    description=validated.get("description", raw_text[:500]),
                    vendor=validated.get("vendor"),
                    product=validated.get("product"),
                    severity=validated.get("severity"),
                    cvss_score=validated.get("cvss_score"),
                    cvss_vector=validated.get("cvss_vector"),
                    confidence_score=confidence,
                    needs_review=needs_review,
                    extraction_metadata={
                        "provider": provider.provider_name,
                        "model": self.model,
                        "temperature": self.temperature,
                        "extraction_time": datetime.utcnow().isoformat(),
                        "provider_metadata": provider_metadata,
                        "validation_issues": validated.get("_validation_issues", []),
                        "fallback_attempt": attempt,
                    }
                )

            except (LLMConnectionError, LLMGenerationError) as e:
                last_error = e
                logger.warning(
                    f"Provider {provider.provider_name} failed (attempt {attempt + 1}): {e}"
                )
                if attempt < len(providers_to_try) - 1:
                    logger.info(f"Trying fallback provider...")
                continue

        # All providers failed - return fallback result
        logger.error(
            f"All {len(providers_to_try)} providers failed. "
            f"Last error: {last_error}"
        )
        return self.extractor._create_fallback_result(
            raw_text,
            f"All providers failed: {str(last_error)}"
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
            batch_size: Number to process concurrently (future enhancement)

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
                results.append(self.extractor._create_fallback_result(text, str(e)))

        return results

    def _build_extraction_prompt(self, raw_text: str) -> str:
        """Build extraction prompt for LLM."""
        return f"""Extract vulnerability information from the following text:

{raw_text}

Return a JSON object with the extracted fields."""

    async def test_primary_provider(self) -> Dict[str, Any]:
        """Test connection to primary provider."""
        try:
            return await self.primary_provider.test_connection()
        except LLMConnectionError as e:
            return {
                "status": "disconnected",
                "provider": self.primary_provider.provider_name,
                "error": str(e),
            }

    async def list_available_models(self) -> Dict[str, Any]:
        """List available models from all configured providers."""
        models_by_provider = {}

        for provider in [self.primary_provider] + self.fallback_providers:
            try:
                models = await provider.list_models()
                models_by_provider[provider.provider_name] = {
                    "status": "connected",
                    "models": models,
                }
            except LLMConnectionError as e:
                models_by_provider[provider.provider_name] = {
                    "status": "disconnected",
                    "error": str(e),
                }

        return models_by_provider


class LLMProviderManager:
    """
    Manager for creating and configuring multi-provider LLM service.

    Handles provider instantiation and configuration from database settings.
    """

    @staticmethod
    def create_from_config(config_dict: Dict[str, Any]) -> MultiProviderLLMService:
        """
        Create multi-provider service from configuration dictionary.

        Args:
            config_dict: Configuration with keys:
                - primary_provider: Provider name ('ollama', 'claude', 'gemini')
                - fallback_providers: List of fallback provider names
                - provider_config: Dict with provider-specific configs
                - model: Model name/ID
                - temperature: Sampling temperature
                - confidence_threshold: Confidence threshold
                - max_tokens: Max tokens per request

        Returns:
            Configured MultiProviderLLMService instance

        Raises:
            ValueError: If configuration is invalid
        """
        primary_name = config_dict.get("primary_provider", "ollama")
        fallback_names = config_dict.get("fallback_providers", [])
        provider_configs = config_dict.get("provider_config", {})

        # Create primary provider
        primary_config = provider_configs.get(primary_name, {})
        timeout = config_dict.get("timeout", 30)
        max_tokens = config_dict.get("max_tokens", 1000)

        if isinstance(primary_config, str):
            # Handle legacy config format
            primary_config = {"base_url": primary_config}

        try:
            primary_provider = LLMProviderFactory.create_provider(
                primary_name,
                timeout=timeout,
                **primary_config
            )
        except Exception as e:
            raise ValueError(
                f"Failed to create primary provider '{primary_name}': {str(e)}"
            ) from e

        # Create fallback providers
        fallback_providers = []
        for fallback_name in fallback_names:
            if not fallback_name or fallback_name == primary_name:
                continue

            fallback_config = provider_configs.get(fallback_name, {})
            if isinstance(fallback_config, str):
                fallback_config = {"base_url": fallback_config}

            try:
                provider = LLMProviderFactory.create_provider(
                    fallback_name,
                    timeout=timeout,
                    **fallback_config
                )
                fallback_providers.append(provider)
            except Exception as e:
                logger.warning(
                    f"Failed to create fallback provider '{fallback_name}': {str(e)}"
                )

        # Create service
        return MultiProviderLLMService(
            primary_provider=primary_provider,
            fallback_providers=fallback_providers,
            model=config_dict.get("model", "auto"),
            temperature=config_dict.get("temperature", 0.1),
            confidence_threshold=config_dict.get("confidence_threshold", 0.8),
            max_retries=config_dict.get("max_retries", 3),
        )

    @staticmethod
    def get_provider_config_template(provider_name: str) -> Dict[str, Any]:
        """
        Get configuration template for a provider.

        Args:
            provider_name: Name of provider

        Returns:
            Template dict with required/optional fields
        """
        templates = {
            "ollama": {
                "description": "Local Ollama LLM server",
                "required": ["base_url"],
                "optional": ["timeout"],
                "example": {
                    "base_url": "http://localhost:11434",
                }
            },
            "claude": {
                "description": "Anthropic Claude API",
                "required": ["api_key"],
                "optional": ["timeout"],
                "example": {
                    "api_key": "sk-ant-...",
                }
            },
            "gemini": {
                "description": "Google Gemini API",
                "required": ["api_key"],
                "optional": ["timeout"],
                "example": {
                    "api_key": "AIzaSy...",
                }
            },
        }

        if provider_name not in templates:
            return {"error": f"Unknown provider: {provider_name}"}

        return templates[provider_name]
