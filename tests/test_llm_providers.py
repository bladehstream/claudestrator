"""
Tests for multi-provider LLM support (Ollama, Claude, Gemini).

Tests:
- Abstract LLM provider interface compliance
- Claude API provider implementation
- Gemini API provider implementation
- Provider fallback logic
- Configuration and factory pattern
"""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.backend.services.llm_providers import (
    LLMProvider,
    OllamaProvider,
    ClaudeProvider,
    GeminiProvider,
    LLMProviderFactory,
    LLMConnectionError,
    LLMGenerationError,
    LLMConfigError,
)

from app.backend.services.llm_multi_provider_service import (
    MultiProviderLLMService,
    LLMProviderManager,
)


# Tests for LLMProvider abstract class
class TestLLMProviderInterface:
    """Test that providers implement the LLM interface."""

    def test_ollama_implements_interface(self):
        """Ollama provider implements LLMProvider."""
        provider = OllamaProvider()
        assert isinstance(provider, LLMProvider)
        assert hasattr(provider, 'test_connection')
        assert hasattr(provider, 'list_models')
        assert hasattr(provider, 'generate_json')
        assert hasattr(provider, 'check_model_available')
        assert provider.provider_name == "ollama"

    def test_claude_implements_interface(self):
        """Claude provider implements LLMProvider."""
        provider = ClaudeProvider(api_key="test-key")
        assert isinstance(provider, LLMProvider)
        assert hasattr(provider, 'test_connection')
        assert hasattr(provider, 'list_models')
        assert hasattr(provider, 'generate_json')
        assert hasattr(provider, 'check_model_available')
        assert provider.provider_name == "claude"

    def test_gemini_implements_interface(self):
        """Gemini provider implements LLMProvider."""
        provider = GeminiProvider(api_key="test-key")
        assert isinstance(provider, LLMProvider)
        assert hasattr(provider, 'test_connection')
        assert hasattr(provider, 'list_models')
        assert hasattr(provider, 'generate_json')
        assert hasattr(provider, 'check_model_available')
        assert provider.provider_name == "gemini"


# Tests for Ollama Provider
class TestOllamaProvider:
    """Test Ollama provider implementation."""

    def test_init_with_valid_url(self):
        """Initialize Ollama with valid URL."""
        provider = OllamaProvider(base_url="http://localhost:11434")
        assert provider.base_url == "http://localhost:11434"

    def test_init_strips_trailing_slash(self):
        """Initialize Ollama strips trailing slash from URL."""
        provider = OllamaProvider(base_url="http://localhost:11434/")
        assert provider.base_url == "http://localhost:11434"

    def test_init_requires_base_url(self):
        """Initialize Ollama fails without base_url."""
        with pytest.raises(LLMConfigError):
            OllamaProvider(base_url="")

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test connection to Ollama succeeds."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": [{"name": "llama3"}]}
            mock_get.return_value.__aenter__.return_value = MagicMock(get=AsyncMock(return_value=mock_response))

            provider = OllamaProvider()
            result = await provider.test_connection()

            assert result["status"] == "connected"
            assert result["provider"] == "ollama"
            assert result["models_count"] == 1

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test connection to Ollama fails."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            provider = OllamaProvider()
            with pytest.raises(LLMConnectionError):
                await provider.test_connection()

    @pytest.mark.asyncio
    async def test_list_models_success(self):
        """List models from Ollama succeeds."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama3", "size": 3800000000, "modified_at": "2024-01-01"}
                ]
            }
            mock_get.return_value.__aenter__.return_value = MagicMock(get=AsyncMock(return_value=mock_response))

            provider = OllamaProvider()
            models = await provider.list_models()

            assert len(models) == 1
            assert models[0]["name"] == "llama3"
            assert models[0]["provider"] == "ollama"


# Tests for Claude Provider
class TestClaudeProvider:
    """Test Claude provider implementation."""

    def test_init_with_valid_key(self):
        """Initialize Claude with valid API key."""
        provider = ClaudeProvider(api_key="sk-ant-test")
        assert provider.api_key == "sk-ant-test"

    def test_init_requires_api_key(self):
        """Initialize Claude fails without API key."""
        with pytest.raises(LLMConfigError):
            ClaudeProvider(api_key="")

    @pytest.mark.asyncio
    async def test_list_models_returns_known_models(self):
        """Claude list_models returns known Claude models."""
        provider = ClaudeProvider(api_key="test-key")
        models = await provider.list_models()

        assert len(models) > 0
        model_names = [m["name"] for m in models]
        assert "claude-3-5-sonnet-20241022" in model_names
        assert all(m["provider"] == "claude" for m in models)

    @pytest.mark.asyncio
    async def test_check_model_available(self):
        """Check if model is available in Claude."""
        provider = ClaudeProvider(api_key="test-key")

        # Should return True for known model
        available = await provider.check_model_available("claude-3-5-sonnet-20241022")
        assert available is True

        # Should return False for unknown model
        available = await provider.check_model_available("unknown-model")
        assert available is False


# Tests for Gemini Provider
class TestGeminiProvider:
    """Test Gemini provider implementation."""

    def test_init_with_valid_key(self):
        """Initialize Gemini with valid API key."""
        provider = GeminiProvider(api_key="AIzaSy...")
        assert provider.api_key == "AIzaSy..."

    def test_init_requires_api_key(self):
        """Initialize Gemini fails without API key."""
        with pytest.raises(LLMConfigError):
            GeminiProvider(api_key="")

    @pytest.mark.asyncio
    async def test_list_models_returns_known_models(self):
        """Gemini list_models returns known Gemini models."""
        provider = GeminiProvider(api_key="test-key")
        models = await provider.list_models()

        assert len(models) > 0
        model_names = [m["name"] for m in models]
        assert "gemini-2.0-flash" in model_names
        assert all(m["provider"] == "gemini" for m in models)

    @pytest.mark.asyncio
    async def test_check_model_available(self):
        """Check if model is available in Gemini."""
        provider = GeminiProvider(api_key="test-key")

        # Should return True for known model
        available = await provider.check_model_available("gemini-2.0-flash")
        assert available is True

        # Should return False for unknown model
        available = await provider.check_model_available("unknown-model")
        assert available is False


# Tests for LLMProviderFactory
class TestLLMProviderFactory:
    """Test provider factory pattern."""

    def test_create_ollama_provider(self):
        """Factory creates Ollama provider."""
        provider = LLMProviderFactory.create_provider("ollama")
        assert isinstance(provider, OllamaProvider)

    def test_create_claude_provider(self):
        """Factory creates Claude provider."""
        provider = LLMProviderFactory.create_provider("claude", api_key="test-key")
        assert isinstance(provider, ClaudeProvider)

    def test_create_gemini_provider(self):
        """Factory creates Gemini provider."""
        provider = LLMProviderFactory.create_provider("gemini", api_key="test-key")
        assert isinstance(provider, GeminiProvider)

    def test_create_unknown_provider_fails(self):
        """Factory raises error for unknown provider."""
        with pytest.raises(LLMConfigError):
            LLMProviderFactory.create_provider("unknown")

    def test_get_available_providers(self):
        """Factory returns list of available providers."""
        providers = LLMProviderFactory.get_available_providers()
        assert "ollama" in providers
        assert "claude" in providers
        assert "gemini" in providers

    def test_register_custom_provider(self):
        """Factory can register custom provider."""
        class CustomProvider(LLMProvider):
            @property
            def provider_name(self):
                return "custom"

            async def test_connection(self):
                pass

            async def list_models(self):
                return []

            async def generate_json(self, **kwargs):
                pass

            async def check_model_available(self, model_name):
                return False

        LLMProviderFactory.register_provider("custom", CustomProvider)
        provider = LLMProviderFactory.create_provider("custom")
        assert isinstance(provider, CustomProvider)


# Tests for MultiProviderLLMService
class TestMultiProviderLLMService:
    """Test multi-provider service with fallback logic."""

    def test_init_with_single_provider(self):
        """Initialize service with single provider."""
        provider = OllamaProvider()
        service = MultiProviderLLMService(primary_provider=provider)

        assert service.primary_provider == provider
        assert service.fallback_providers == []

    def test_init_with_fallback_providers(self):
        """Initialize service with fallback providers."""
        primary = OllamaProvider()
        fallbacks = [
            ClaudeProvider(api_key="test"),
            GeminiProvider(api_key="test"),
        ]
        service = MultiProviderLLMService(
            primary_provider=primary,
            fallback_providers=fallbacks
        )

        assert service.primary_provider == primary
        assert len(service.fallback_providers) == 2

    @pytest.mark.asyncio
    async def test_extract_with_primary_provider(self):
        """Extract uses primary provider when available."""
        provider = MagicMock(spec=OllamaProvider)
        provider.provider_name = "ollama"
        provider.generate_json = AsyncMock(return_value={
            "data": {
                "cve_id": "CVE-2024-1234",
                "title": "Test CVE",
                "description": "Test description",
                "vendor": "Test Vendor",
                "product": "Test Product",
                "severity": "HIGH",
                "cvss_score": 7.5,
                "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H",
            },
            "metadata": {"model": "test", "total_duration_ms": 100},
        })

        service = MultiProviderLLMService(primary_provider=provider)
        result = await service.extract_vulnerability("CVE-2024-1234: Test vulnerability")

        assert result.cve_id == "CVE-2024-1234"
        assert provider.generate_json.called

    @pytest.mark.asyncio
    async def test_extract_falls_back_on_primary_failure(self):
        """Extract falls back to fallback provider if primary fails."""
        primary = MagicMock(spec=OllamaProvider)
        primary.provider_name = "ollama"
        primary.generate_json = AsyncMock(side_effect=LLMGenerationError("Primary failed"))

        fallback = MagicMock(spec=ClaudeProvider)
        fallback.provider_name = "claude"
        fallback.generate_json = AsyncMock(return_value={
            "data": {
                "cve_id": "CVE-2024-1234",
                "title": "Test",
                "description": "Fallback extraction",
                "severity": "UNKNOWN",
            },
            "metadata": {"model": "claude", "input_tokens": 10, "output_tokens": 20},
        })

        service = MultiProviderLLMService(
            primary_provider=primary,
            fallback_providers=[fallback]
        )

        result = await service.extract_vulnerability("CVE-2024-1234: Test")

        assert fallback.generate_json.called
        assert result.extraction_metadata["fallback_attempt"] > 0

    @pytest.mark.asyncio
    async def test_extract_all_providers_fail(self):
        """Extract creates fallback result if all providers fail."""
        primary = MagicMock(spec=OllamaProvider)
        primary.provider_name = "ollama"
        primary.generate_json = AsyncMock(side_effect=LLMGenerationError("Failed"))

        fallback = MagicMock(spec=ClaudeProvider)
        fallback.provider_name = "claude"
        fallback.generate_json = AsyncMock(side_effect=LLMGenerationError("Also failed"))

        service = MultiProviderLLMService(
            primary_provider=primary,
            fallback_providers=[fallback]
        )

        result = await service.extract_vulnerability("CVE-2024-1234: Test")

        # Should create fallback result with CVE extracted from raw text
        assert result.cve_id == "CVE-2024-1234"
        assert result.confidence_score == 0.1  # Low confidence for fallback


# Tests for LLMProviderManager
class TestLLMProviderManager:
    """Test provider manager and configuration."""

    def test_create_from_config_ollama(self):
        """Create service from Ollama config."""
        config = {
            "primary_provider": "ollama",
            "provider_config": {
                "ollama": {"base_url": "http://localhost:11434"}
            },
            "model": "llama3",
            "temperature": 0.1,
        }

        service = LLMProviderManager.create_from_config(config)
        assert isinstance(service.primary_provider, OllamaProvider)

    def test_create_from_config_with_fallbacks(self):
        """Create service with fallback providers from config."""
        config = {
            "primary_provider": "ollama",
            "fallback_providers": ["claude", "gemini"],
            "provider_config": {
                "ollama": {"base_url": "http://localhost:11434"},
                "claude": {"api_key": "sk-ant-test"},
                "gemini": {"api_key": "AIzaSy-test"},
            },
            "model": "auto",
        }

        service = LLMProviderManager.create_from_config(config)
        assert len(service.fallback_providers) == 2

    def test_get_provider_template_ollama(self):
        """Get configuration template for Ollama."""
        template = LLMProviderManager.get_provider_config_template("ollama")
        assert "description" in template
        assert "base_url" in template["required"]

    def test_get_provider_template_claude(self):
        """Get configuration template for Claude."""
        template = LLMProviderManager.get_provider_config_template("claude")
        assert "description" in template
        assert "api_key" in template["required"]

    def test_get_provider_template_gemini(self):
        """Get configuration template for Gemini."""
        template = LLMProviderManager.get_provider_config_template("gemini")
        assert "description" in template
        assert "api_key" in template["required"]

    def test_get_provider_template_unknown(self):
        """Get template for unknown provider returns error."""
        template = LLMProviderManager.get_provider_config_template("unknown")
        assert "error" in template


# Integration tests
class TestMultiProviderIntegration:
    """Integration tests for multi-provider system."""

    @pytest.mark.asyncio
    async def test_batch_extract_with_multiple_entries(self):
        """Batch extract processes multiple entries."""
        provider = MagicMock(spec=OllamaProvider)
        provider.provider_name = "ollama"
        provider.generate_json = AsyncMock(return_value={
            "data": {
                "cve_id": "CVE-2024-9999",
                "description": "Test",
                "severity": "UNKNOWN",
            },
            "metadata": {"model": "test"},
        })

        service = MultiProviderLLMService(primary_provider=provider)
        texts = [
            "CVE-2024-0001: First CVE",
            "CVE-2024-0002: Second CVE",
        ]

        results = await service.batch_extract(texts)

        assert len(results) == 2
        assert provider.generate_json.call_count == 2

    def test_provider_name_consistency(self):
        """All providers have consistent provider_name property."""
        providers = [
            OllamaProvider(),
            ClaudeProvider(api_key="test"),
            GeminiProvider(api_key="test"),
        ]

        names = {p.provider_name for p in providers}
        assert names == {"ollama", "claude", "gemini"}
