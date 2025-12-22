"""
Tests for Ollama client.

Tests connection, model discovery, and generation capabilities.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.backend.services.ollama_client import (
    OllamaClient,
    OllamaConnectionError,
    OllamaModelError
)


@pytest.fixture
def ollama_client():
    """Create Ollama client for testing."""
    return OllamaClient(base_url="http://localhost:11434", timeout=30)


@pytest.mark.asyncio
class TestOllamaClient:
    """Test suite for OllamaClient."""

    async def test_test_connection_success(self, ollama_client):
        """Test successful connection to Ollama server."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3", "size": 1000000},
                {"name": "mistral", "size": 2000000}
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.get.return_value = mock_response
            mock_client.return_value = mock_instance

            result = await ollama_client.test_connection()

            assert result["status"] == "connected"
            assert result["models_count"] == 2
            assert result["server"] == "http://localhost:11434"

    async def test_test_connection_failure(self, ollama_client):
        """Test connection failure handling."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client.return_value = mock_instance

            with pytest.raises(OllamaConnectionError) as exc_info:
                await ollama_client.test_connection()

            assert "Cannot connect to Ollama" in str(exc_info.value)

    async def test_list_models_success(self, ollama_client):
        """Test successful model listing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "llama3",
                    "model": "llama3:latest",
                    "size": 3800000000,
                    "modified_at": "2024-01-01T00:00:00Z",
                    "digest": "abc123def456789"
                },
                {
                    "name": "mistral",
                    "model": "mistral:latest",
                    "size": 4100000000,
                    "modified_at": "2024-01-02T00:00:00Z",
                    "digest": "xyz987uvw654321"
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.get.return_value = mock_response
            mock_client.return_value = mock_instance

            models = await ollama_client.list_models()

            assert len(models) == 2
            assert models[0]["name"] == "llama3"
            assert models[1]["name"] == "mistral"
            assert "digest" in models[0]

    async def test_generate_success(self, ollama_client):
        """Test successful text generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3",
            "response": "This is a test response",
            "created_at": "2024-01-01T00:00:00Z",
            "done": True,
            "total_duration": 1500000000,  # 1.5 seconds in nanoseconds
            "eval_count": 50
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            result = await ollama_client.generate(
                model="llama3",
                prompt="Test prompt",
                temperature=0.1
            )

            assert result["response"] == "This is a test response"
            assert result["metadata"]["model"] == "llama3"
            assert result["metadata"]["done"] is True
            assert result["metadata"]["total_duration_ms"] == 1500

    async def test_generate_json_success(self, ollama_client):
        """Test successful JSON generation and parsing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3",
            "response": '{"cve_id": "CVE-2024-1234", "severity": "HIGH"}',
            "created_at": "2024-01-01T00:00:00Z",
            "done": True,
            "total_duration": 2000000000,
            "eval_count": 75
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            result = await ollama_client.generate_json(
                model="llama3",
                prompt="Extract vulnerability data",
                temperature=0.1
            )

            assert result["data"]["cve_id"] == "CVE-2024-1234"
            assert result["data"]["severity"] == "HIGH"
            assert result["metadata"]["model"] == "llama3"

    async def test_generate_json_invalid_response(self, ollama_client):
        """Test JSON parsing failure handling."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3",
            "response": "This is not JSON",
            "created_at": "2024-01-01T00:00:00Z",
            "done": True,
            "total_duration": 1000000000,
            "eval_count": 25
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            with pytest.raises(OllamaModelError) as exc_info:
                await ollama_client.generate_json(
                    model="llama3",
                    prompt="Test prompt"
                )

            assert "did not return valid JSON" in str(exc_info.value)

    async def test_check_model_available(self, ollama_client):
        """Test model availability check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3", "model": "llama3:latest"},
                {"name": "mistral", "model": "mistral:latest"}
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.get.return_value = mock_response
            mock_client.return_value = mock_instance

            # Check existing model
            available = await ollama_client.check_model_available("llama3")
            assert available is True

            # Check non-existing model
            available = await ollama_client.check_model_available("gpt4")
            assert available is False
