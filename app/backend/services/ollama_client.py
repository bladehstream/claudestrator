"""
Ollama client for LLM model discovery and inference.
Handles connection testing, model listing, and structured text generation.
"""

import logging
from typing import Dict, List, Optional, Any
import httpx
import json

logger = logging.getLogger(__name__)


class OllamaClientError(Exception):
    """Base exception for Ollama client errors."""
    pass


class OllamaConnectionError(OllamaClientError):
    """Raised when connection to Ollama server fails."""
    pass


class OllamaModelError(OllamaClientError):
    """Raised when model operations fail."""
    pass


class OllamaClient:
    """
    Client for interacting with Ollama LLM server.

    Provides methods for:
    - Testing connection to Ollama server
    - Discovering available models
    - Generating structured completions
    """

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30):
        """
        Initialize Ollama client.

        Args:
            base_url: Base URL of Ollama server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Ollama server.

        Returns:
            Dict with status and version info

        Raises:
            OllamaConnectionError: If connection fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "connected",
                        "models_count": len(data.get("models", [])),
                        "server": self.base_url
                    }
                else:
                    raise OllamaConnectionError(
                        f"Unexpected status code: {response.status_code}"
                    )

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            raise OllamaConnectionError(
                f"Cannot connect to Ollama server at {self.base_url}. "
                "Ensure Ollama is running and accessible."
            ) from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to Ollama: {e}")
            raise OllamaConnectionError(
                f"Timeout connecting to Ollama server (>{self.timeout}s)"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error testing Ollama connection: {e}")
            raise OllamaConnectionError(f"Connection test failed: {str(e)}") from e

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Discover available models on Ollama server.

        Returns:
            List of model dictionaries with name, size, modified date

        Raises:
            OllamaConnectionError: If connection fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")

                if response.status_code != 200:
                    raise OllamaConnectionError(
                        f"Failed to list models: HTTP {response.status_code}"
                    )

                data = response.json()
                models = data.get("models", [])

                # Format model info for easier consumption
                formatted_models = []
                for model in models:
                    formatted_models.append({
                        "name": model.get("name", "unknown"),
                        "model": model.get("model", ""),
                        "size": model.get("size", 0),
                        "modified_at": model.get("modified_at", ""),
                        "digest": model.get("digest", "")[:12],  # Short digest
                    })

                return formatted_models

        except httpx.HTTPError as e:
            logger.error(f"HTTP error listing models: {e}")
            raise OllamaConnectionError(f"Failed to list models: {str(e)}") from e

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate completion from Ollama model.

        Args:
            model: Model name (e.g., 'llama3', 'mistral')
            prompt: User prompt
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system/context prompt

        Returns:
            Dict with 'response' (str) and 'metadata' (dict)

        Raises:
            OllamaModelError: If generation fails
        """
        try:
            # Build request payload
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

            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:  # Longer timeout for generation
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )

                if response.status_code != 200:
                    error_detail = response.text
                    raise OllamaModelError(
                        f"Generation failed: HTTP {response.status_code} - {error_detail}"
                    )

                data = response.json()

                return {
                    "response": data.get("response", ""),
                    "metadata": {
                        "model": data.get("model", model),
                        "created_at": data.get("created_at", ""),
                        "done": data.get("done", False),
                        "total_duration_ms": data.get("total_duration", 0) / 1000000,  # Convert to ms
                        "eval_count": data.get("eval_count", 0),
                    }
                }

        except httpx.TimeoutException as e:
            logger.error(f"Timeout during generation with model {model}: {e}")
            raise OllamaModelError(
                f"Generation timeout (>{self.timeout * 2}s) for model '{model}'"
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during generation: {e}")
            raise OllamaModelError(f"Generation failed: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Ollama: {e}")
            raise OllamaModelError("Invalid response from Ollama server") from e

    async def generate_json(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output from model.

        Similar to generate() but expects and parses JSON response.

        Args:
            model: Model name
            prompt: User prompt (should request JSON output)
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Parsed JSON object

        Raises:
            OllamaModelError: If generation or JSON parsing fails
        """
        result = await self.generate(
            model=model,
            prompt=prompt,
            temperature=temperature,
            system_prompt=system_prompt,
        )

        response_text = result["response"].strip()

        # Try to extract JSON from response (handles cases where model adds explanation)
        try:
            # Look for JSON object in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1

            if start != -1 and end > start:
                json_str = response_text[start:end]
                parsed = json.loads(json_str)
                return {
                    "data": parsed,
                    "metadata": result["metadata"]
                }
            else:
                raise ValueError("No JSON object found in response")

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse JSON from model response: {e}\nResponse: {response_text[:200]}")
            raise OllamaModelError(
                f"Model did not return valid JSON. Response preview: {response_text[:100]}"
            ) from e

    async def check_model_available(self, model_name: str) -> bool:
        """
        Check if a specific model is available.

        Args:
            model_name: Name of model to check

        Returns:
            True if model is available, False otherwise
        """
        try:
            models = await self.list_models()
            return any(m["name"] == model_name for m in models)
        except OllamaConnectionError:
            return False
