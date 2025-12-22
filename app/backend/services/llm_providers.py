"""
Abstract LLM provider interface and concrete implementations.

Supports multiple LLM providers:
- Ollama (local, open-source)
- Claude (Anthropic API)
- Gemini (Google API)

Each provider implements a common interface for:
- Connection testing
- Model discovery
- Structured JSON generation
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import json
import httpx

logger = logging.getLogger(__name__)


# Base Exceptions
class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMConnectionError(LLMProviderError):
    """Raised when connection to LLM provider fails."""
    pass


class LLMGenerationError(LLMProviderError):
    """Raised when text generation fails."""
    pass


class LLMConfigError(LLMProviderError):
    """Raised when provider configuration is invalid."""
    pass


# Abstract Base Class
class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, timeout: int = 30):
        """
        Initialize LLM provider.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to LLM provider.

        Returns:
            Dict with connection status and provider info

        Raises:
            LLMConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models from provider.

        Returns:
            List of model dictionaries

        Raises:
            LLMConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def generate_json(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output from model.

        Args:
            model: Model name/ID
            prompt: User prompt (should request JSON output)
            system_prompt: Optional system/context prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with 'data' (parsed JSON) and 'metadata' (dict)

        Raises:
            LLMGenerationError: If generation or parsing fails
        """
        pass

    @abstractmethod
    async def check_model_available(self, model_name: str) -> bool:
        """
        Check if a specific model is available.

        Args:
            model_name: Name of model to check

        Returns:
            True if model is available, False otherwise
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g., 'ollama', 'claude', 'gemini')."""
        pass


# Ollama Implementation
class OllamaProvider(LLMProvider):
    """Ollama LLM provider implementation."""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30):
        """
        Initialize Ollama provider.

        Args:
            base_url: Base URL of Ollama server
            timeout: Request timeout in seconds

        Raises:
            LLMConfigError: If base_url is empty
        """
        super().__init__(timeout)
        if not base_url:
            raise LLMConfigError("Ollama base_url is required")
        self.base_url = base_url.rstrip('/')

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Ollama server."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "connected",
                        "provider": self.provider_name,
                        "server": self.base_url,
                        "models_count": len(data.get("models", [])),
                    }
                else:
                    raise LLMConnectionError(
                        f"Unexpected status code: {response.status_code}"
                    )

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            raise LLMConnectionError(
                f"Cannot connect to Ollama server at {self.base_url}"
            ) from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to Ollama: {e}")
            raise LLMConnectionError(
                f"Timeout connecting to Ollama (>{self.timeout}s)"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error testing Ollama connection: {e}")
            raise LLMConnectionError(f"Connection test failed: {str(e)}") from e

    async def list_models(self) -> List[Dict[str, Any]]:
        """Discover available models on Ollama server."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")

                if response.status_code != 200:
                    raise LLMConnectionError(
                        f"Failed to list models: HTTP {response.status_code}"
                    )

                data = response.json()
                models = data.get("models", [])

                formatted_models = []
                for model in models:
                    formatted_models.append({
                        "name": model.get("name", "unknown"),
                        "model": model.get("model", ""),
                        "size": model.get("size", 0),
                        "modified_at": model.get("modified_at", ""),
                        "provider": self.provider_name,
                    })

                return formatted_models

        except httpx.HTTPError as e:
            logger.error(f"HTTP error listing models: {e}")
            raise LLMConnectionError(f"Failed to list models: {str(e)}") from e

    async def generate_json(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON output from Ollama model."""
        try:
            # First, generate text response
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            if system_prompt:
                payload["system"] = system_prompt

            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )

                if response.status_code != 200:
                    raise LLMGenerationError(
                        f"Generation failed: HTTP {response.status_code}"
                    )

                data = response.json()
                response_text = data.get("response", "").strip()

                # Extract and parse JSON
                start = response_text.find('{')
                end = response_text.rfind('}') + 1

                if start == -1 or end <= start:
                    raise LLMGenerationError("No JSON object found in response")

                json_str = response_text[start:end]
                parsed = json.loads(json_str)

                return {
                    "data": parsed,
                    "metadata": {
                        "provider": self.provider_name,
                        "model": model,
                        "total_duration_ms": data.get("total_duration", 0) / 1000000,
                        "eval_count": data.get("eval_count", 0),
                    }
                }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Ollama response: {e}")
            raise LLMGenerationError(f"Invalid JSON in response: {str(e)}") from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout during Ollama generation: {e}")
            raise LLMGenerationError(f"Generation timeout (>{self.timeout * 2}s)") from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Ollama generation: {e}")
            raise LLMGenerationError(f"Generation failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in Ollama generation: {e}")
            raise LLMGenerationError(f"Generation failed: {str(e)}") from e

    async def check_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available on Ollama."""
        try:
            models = await self.list_models()
            return any(m["name"] == model_name for m in models)
        except LLMConnectionError:
            return False


# Claude Implementation
class ClaudeProvider(LLMProvider):
    """Claude (Anthropic) LLM provider implementation."""

    # Latest Claude model as of knowledge cutoff
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key
            timeout: Request timeout in seconds

        Raises:
            LLMConfigError: If api_key is empty
        """
        super().__init__(timeout)
        if not api_key:
            raise LLMConfigError("Claude API key is required")
        self.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "claude"

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Claude API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }

                payload = {
                    "model": self.DEFAULT_MODEL,
                    "max_tokens": 100,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Test connection"
                        }
                    ]
                }

                response = await client.post(
                    self.API_URL,
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    return {
                        "status": "connected",
                        "provider": self.provider_name,
                        "model": self.DEFAULT_MODEL,
                    }
                else:
                    error_detail = response.text
                    raise LLMConnectionError(
                        f"API returned status {response.status_code}: {error_detail}"
                    )

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Claude API: {e}")
            raise LLMConnectionError("Cannot connect to Claude API") from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to Claude API: {e}")
            raise LLMConnectionError(f"Timeout connecting to Claude (>{self.timeout}s)") from e
        except Exception as e:
            logger.error(f"Unexpected error testing Claude connection: {e}")
            raise LLMConnectionError(f"Connection test failed: {str(e)}") from e

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available Claude models.

        Note: Claude API doesn't provide a models endpoint,
        so we return known Claude models.
        """
        return [
            {
                "name": "claude-3-5-sonnet-20241022",
                "display_name": "Claude 3.5 Sonnet",
                "provider": self.provider_name,
                "context_window": 200000,
            },
            {
                "name": "claude-3-opus-20250219",
                "display_name": "Claude 3 Opus",
                "provider": self.provider_name,
                "context_window": 200000,
            },
            {
                "name": "claude-3-haiku-20250307",
                "display_name": "Claude 3 Haiku",
                "provider": self.provider_name,
                "context_window": 200000,
            },
        ]

    async def generate_json(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON output from Claude."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }

                # Prepare messages
                messages = []
                if system_prompt:
                    # Note: Claude uses system parameter, not system message
                    pass  # Handled below

                messages.append({
                    "role": "user",
                    "content": prompt
                })

                payload = {
                    "model": model,
                    "max_tokens": max_tokens or 4000,
                    "temperature": temperature,
                    "messages": messages,
                }

                if system_prompt:
                    payload["system"] = system_prompt

                response = await client.post(
                    self.API_URL,
                    json=payload,
                    headers=headers
                )

                if response.status_code != 200:
                    error_detail = response.text
                    raise LLMGenerationError(
                        f"Generation failed: HTTP {response.status_code} - {error_detail}"
                    )

                data = response.json()

                # Extract response text from Claude's format
                response_text = ""
                if "content" in data and isinstance(data["content"], list):
                    for content in data["content"]:
                        if content.get("type") == "text":
                            response_text = content.get("text", "")
                            break

                if not response_text:
                    raise LLMGenerationError("No text response from Claude")

                # Extract and parse JSON
                start = response_text.find('{')
                end = response_text.rfind('}') + 1

                if start == -1 or end <= start:
                    raise LLMGenerationError("No JSON object found in response")

                json_str = response_text[start:end]
                parsed = json.loads(json_str)

                return {
                    "data": parsed,
                    "metadata": {
                        "provider": self.provider_name,
                        "model": model,
                        "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": data.get("usage", {}).get("output_tokens", 0),
                    }
                }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            raise LLMGenerationError(f"Invalid JSON in response: {str(e)}") from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout during Claude generation: {e}")
            raise LLMGenerationError(f"Generation timeout (>{self.timeout * 2}s)") from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Claude generation: {e}")
            raise LLMGenerationError(f"Generation failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in Claude generation: {e}")
            raise LLMGenerationError(f"Generation failed: {str(e)}") from e

    async def check_model_available(self, model_name: str) -> bool:
        """Check if a specific Claude model is available."""
        models = await self.list_models()
        return any(m["name"] == model_name for m in models)


# Gemini Implementation
class GeminiProvider(LLMProvider):
    """Gemini (Google) LLM provider implementation."""

    # Latest Gemini model
    DEFAULT_MODEL = "gemini-2.0-flash"
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key for Gemini
            timeout: Request timeout in seconds

        Raises:
            LLMConfigError: If api_key is empty
        """
        super().__init__(timeout)
        if not api_key:
            raise LLMConfigError("Gemini API key is required")
        self.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Gemini API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Simple test by calling generate
                url = f"{self.API_URL}/{self.DEFAULT_MODEL}:generateContent?key={self.api_key}"

                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": "Test connection"
                                }
                            ]
                        }
                    ]
                }

                response = await client.post(
                    url,
                    json=payload
                )

                if response.status_code == 200:
                    return {
                        "status": "connected",
                        "provider": self.provider_name,
                        "model": self.DEFAULT_MODEL,
                    }
                else:
                    error_detail = response.text
                    raise LLMConnectionError(
                        f"API returned status {response.status_code}: {error_detail}"
                    )

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Gemini API: {e}")
            raise LLMConnectionError("Cannot connect to Gemini API") from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to Gemini API: {e}")
            raise LLMConnectionError(f"Timeout connecting to Gemini (>{self.timeout}s)") from e
        except Exception as e:
            logger.error(f"Unexpected error testing Gemini connection: {e}")
            raise LLMConnectionError(f"Connection test failed: {str(e)}") from e

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available Gemini models.

        Note: Gemini API doesn't provide a models list endpoint,
        so we return known Gemini models.
        """
        return [
            {
                "name": "gemini-2.0-flash",
                "display_name": "Gemini 2.0 Flash",
                "provider": self.provider_name,
                "context_window": 1000000,
            },
            {
                "name": "gemini-1.5-pro",
                "display_name": "Gemini 1.5 Pro",
                "provider": self.provider_name,
                "context_window": 1000000,
            },
            {
                "name": "gemini-1.5-flash",
                "display_name": "Gemini 1.5 Flash",
                "provider": self.provider_name,
                "context_window": 1000000,
            },
        ]

    async def generate_json(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON output from Gemini."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                url = f"{self.API_URL}/{model}:generateContent?key={self.api_key}"

                # Prepare content
                parts = []

                if system_prompt:
                    parts.append({
                        "text": f"System: {system_prompt}\n\nUser: {prompt}"
                    })
                else:
                    parts.append({
                        "text": prompt
                    })

                payload = {
                    "contents": [
                        {
                            "parts": parts
                        }
                    ],
                    "generationConfig": {
                        "temperature": temperature,
                    }
                }

                if max_tokens:
                    payload["generationConfig"]["maxOutputTokens"] = max_tokens

                response = await client.post(
                    url,
                    json=payload
                )

                if response.status_code != 200:
                    error_detail = response.text
                    raise LLMGenerationError(
                        f"Generation failed: HTTP {response.status_code} - {error_detail}"
                    )

                data = response.json()

                # Extract response text from Gemini's format
                response_text = ""
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                response_text = part["text"]
                                break

                if not response_text:
                    raise LLMGenerationError("No text response from Gemini")

                # Extract and parse JSON
                start = response_text.find('{')
                end = response_text.rfind('}') + 1

                if start == -1 or end <= start:
                    raise LLMGenerationError("No JSON object found in response")

                json_str = response_text[start:end]
                parsed = json.loads(json_str)

                return {
                    "data": parsed,
                    "metadata": {
                        "provider": self.provider_name,
                        "model": model,
                        "usage_tokens": data.get("usageMetadata", {}).get("totalTokenCount", 0),
                    }
                }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            raise LLMGenerationError(f"Invalid JSON in response: {str(e)}") from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout during Gemini generation: {e}")
            raise LLMGenerationError(f"Generation timeout (>{self.timeout * 2}s)") from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during Gemini generation: {e}")
            raise LLMGenerationError(f"Generation failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in Gemini generation: {e}")
            raise LLMGenerationError(f"Generation failed: {str(e)}") from e

    async def check_model_available(self, model_name: str) -> bool:
        """Check if a specific Gemini model is available."""
        models = await self.list_models()
        return any(m["name"] == model_name for m in models)


# Provider Factory
class LLMProviderFactory:
    """Factory for creating and managing LLM providers."""

    _PROVIDERS = {
        "ollama": OllamaProvider,
        "claude": ClaudeProvider,
        "gemini": GeminiProvider,
    }

    @classmethod
    def create_provider(
        cls,
        provider_type: str,
        **kwargs
    ) -> LLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_type: Type of provider ('ollama', 'claude', 'gemini')
            **kwargs: Provider-specific configuration

        Returns:
            Configured LLM provider instance

        Raises:
            LLMConfigError: If provider_type is unknown or config is invalid
        """
        if provider_type not in cls._PROVIDERS:
            available = ", ".join(cls._PROVIDERS.keys())
            raise LLMConfigError(
                f"Unknown provider: {provider_type}. Available: {available}"
            )

        provider_class = cls._PROVIDERS[provider_type]
        try:
            return provider_class(**kwargs)
        except TypeError as e:
            raise LLMConfigError(
                f"Invalid configuration for {provider_type}: {str(e)}"
            ) from e

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """Register a new provider class."""
        if not issubclass(provider_class, LLMProvider):
            raise LLMConfigError(
                f"{provider_class} must inherit from LLMProvider"
            )
        cls._PROVIDERS[name] = provider_class

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of registered provider names."""
        return list(cls._PROVIDERS.keys())
