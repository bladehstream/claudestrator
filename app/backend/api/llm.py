"""
Admin API endpoints for LLM configuration and management.

Endpoints:
- GET /admin/llm/config - Get current LLM configuration
- POST /admin/llm/config - Update LLM configuration
- GET /admin/llm/test - Test connection to Ollama server
- GET /admin/llm/models - List available models
- POST /admin/llm/test-extract - Test extraction on sample text
"""

import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.backend.database import get_db
from app.backend.models import LLMConfig
from app.backend.services.ollama_client import OllamaClient, OllamaConnectionError, OllamaModelError
from app.backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/llm", tags=["LLM Admin"])


# Request/Response Models
class LLMConfigUpdate(BaseModel):
    """Request model for updating LLM configuration."""
    ollama_base_url: Optional[str] = Field(None, description="Ollama server URL")
    selected_model: Optional[str] = Field(None, description="Model to use for extraction")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=100, le=4000, description="Max tokens per request")
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence threshold")
    processing_interval_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Processing interval")
    batch_size: Optional[int] = Field(None, ge=1, le=100, description="Batch processing size")


class LLMConfigResponse(BaseModel):
    """Response model for LLM configuration."""
    id: int
    ollama_base_url: str
    selected_model: Optional[str]
    temperature: float
    max_tokens: int
    confidence_threshold: float
    processing_interval_minutes: int
    batch_size: int
    connection_status: str
    last_connection_test: Optional[str]
    available_models: Optional[list]

    class Config:
        from_attributes = True


class ConnectionTestResponse(BaseModel):
    """Response model for connection test."""
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ModelListResponse(BaseModel):
    """Response model for model list."""
    models: list
    count: int


class TestExtractionRequest(BaseModel):
    """Request model for testing extraction."""
    raw_text: str = Field(..., min_length=10, description="Sample vulnerability text")
    model: Optional[str] = Field(None, description="Override model for test")


class TestExtractionResponse(BaseModel):
    """Response model for test extraction."""
    success: bool
    extraction: Optional[Dict[str, Any]]
    error: Optional[str]


# Helper functions
async def get_or_create_config(db: AsyncSession) -> LLMConfig:
    """Get existing LLM config or create default."""
    result = await db.execute(select(LLMConfig))
    config = result.scalar_one_or_none()

    if not config:
        config = LLMConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config


# Endpoints
@router.get("/config", response_model=LLMConfigResponse)
async def get_llm_config(db: AsyncSession = Depends(get_db)):
    """
    Get current LLM configuration.

    Returns configuration for Ollama connection and processing parameters.
    """
    config = await get_or_create_config(db)
    return config


@router.post("/config", response_model=LLMConfigResponse)
async def update_llm_config(
    updates: LLMConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update LLM configuration.

    Allows updating Ollama connection details and processing parameters.
    """
    config = await get_or_create_config(db)

    # Apply updates
    if updates.ollama_base_url is not None:
        config.ollama_base_url = updates.ollama_base_url.rstrip('/')

    if updates.selected_model is not None:
        config.selected_model = updates.selected_model

    if updates.temperature is not None:
        config.temperature = updates.temperature

    if updates.max_tokens is not None:
        config.max_tokens = updates.max_tokens

    if updates.confidence_threshold is not None:
        config.confidence_threshold = updates.confidence_threshold

    if updates.processing_interval_minutes is not None:
        config.processing_interval_minutes = updates.processing_interval_minutes

    if updates.batch_size is not None:
        config.batch_size = updates.batch_size

    await db.commit()
    await db.refresh(config)

    logger.info(f"LLM configuration updated: {config}")

    return config


@router.get("/test", response_model=ConnectionTestResponse)
async def test_connection(db: AsyncSession = Depends(get_db)):
    """
    Test connection to Ollama server.

    Attempts to connect to configured Ollama instance and retrieve server info.
    """
    config = await get_or_create_config(db)

    client = OllamaClient(base_url=config.ollama_base_url, timeout=10)

    try:
        result = await client.test_connection()

        # Update config with test results
        from datetime import datetime
        config.last_connection_test = datetime.utcnow()
        config.connection_status = "connected"
        await db.commit()

        return ConnectionTestResponse(
            status="success",
            message=f"Successfully connected to Ollama at {config.ollama_base_url}",
            details=result
        )

    except OllamaConnectionError as e:
        config.connection_status = "failed"
        await db.commit()

        return ConnectionTestResponse(
            status="error",
            message=str(e),
            details={"url": config.ollama_base_url}
        )


@router.get("/models", response_model=ModelListResponse)
async def list_models(db: AsyncSession = Depends(get_db)):
    """
    List available models on Ollama server.

    Discovers all models available on the configured Ollama instance.
    """
    config = await get_or_create_config(db)

    client = OllamaClient(base_url=config.ollama_base_url, timeout=10)

    try:
        models = await client.list_models()

        # Update config with available models
        from datetime import datetime
        config.available_models = [m["name"] for m in models]
        config.last_connection_test = datetime.utcnow()
        config.connection_status = "connected"
        await db.commit()

        return ModelListResponse(
            models=models,
            count=len(models)
        )

    except OllamaConnectionError as e:
        config.connection_status = "failed"
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to Ollama: {str(e)}"
        )


@router.post("/test-extract", response_model=TestExtractionResponse)
async def test_extraction(
    request: TestExtractionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Test LLM extraction on sample text.

    Allows testing the extraction pipeline with custom text before processing real entries.
    """
    config = await get_or_create_config(db)

    # Use specified model or configured model
    model = request.model or config.selected_model

    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No model specified and no default model configured"
        )

    client = OllamaClient(base_url=config.ollama_base_url, timeout=30)

    # Check if model is available
    try:
        if not await client.check_model_available(model):
            available = await client.list_models()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{model}' not available. Available models: {[m['name'] for m in available]}"
            )
    except OllamaConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot connect to Ollama: {str(e)}"
        )

    # Perform extraction
    llm_service = LLMService(
        ollama_client=client,
        model=model,
        temperature=config.temperature,
        confidence_threshold=config.confidence_threshold,
    )

    try:
        result = await llm_service.extract_vulnerability(request.raw_text)

        return TestExtractionResponse(
            success=True,
            extraction=result.to_dict(),
            error=None
        )

    except OllamaModelError as e:
        logger.error(f"Test extraction failed: {e}")
        return TestExtractionResponse(
            success=False,
            extraction=None,
            error=str(e)
        )
