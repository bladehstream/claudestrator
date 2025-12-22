"""
Admin API endpoints for multi-provider LLM configuration and management.

Endpoints:
- GET/POST /admin/llm/config - Get/update LLM configuration
- GET /admin/llm/providers - List available providers and configuration templates
- GET /admin/llm/test - Test connection to current provider
- GET /admin/llm/test-all - Test all configured providers
- GET /admin/llm/models - List models from all providers
- POST /admin/llm/test-extract - Test extraction on sample text
"""

import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.backend.database import get_db
from app.backend.models import LLMConfig
from app.backend.services.llm_providers import (
    LLMProviderFactory,
    LLMConnectionError,
    LLMGenerationError,
)
from app.backend.services.llm_multi_provider_service import (
    LLMProviderManager,
    MultiProviderLLMService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/llm", tags=["LLM Admin"])


# Request/Response Models
class ProviderConfig(BaseModel):
    """Configuration for a specific LLM provider."""
    provider: str = Field(..., description="Provider name: 'ollama', 'claude', 'gemini'")
    config: Dict[str, Any] = Field(..., description="Provider-specific configuration")


class LLMConfigUpdate(BaseModel):
    """Request model for updating LLM configuration."""
    primary_provider: Optional[str] = Field(None, description="Primary provider")
    fallback_providers: Optional[List[str]] = Field(None, description="List of fallback providers")
    provider_config: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Provider configs")
    selected_model: Optional[str] = Field(None, description="Model to use for extraction")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=100, le=4000, description="Max tokens per request")
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence threshold")
    processing_interval_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Processing interval")
    batch_size: Optional[int] = Field(None, ge=1, le=100, description="Batch processing size")


class LLMConfigResponse(BaseModel):
    """Response model for LLM configuration."""
    id: int
    primary_provider: str
    fallback_providers: Optional[str]
    provider_config: Dict[str, Any]
    selected_model: Optional[str]
    temperature: float
    max_tokens: int
    confidence_threshold: float
    processing_interval_minutes: int
    batch_size: int
    connection_status: str
    last_connection_test: Optional[str]
    available_models: Optional[dict]

    class Config:
        from_attributes = True


class ProviderStatus(BaseModel):
    """Status of a single provider."""
    provider: str
    status: str  # 'connected', 'disconnected', 'testing'
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class MultiProviderStatus(BaseModel):
    """Status of all configured providers."""
    primary: ProviderStatus
    fallbacks: List[ProviderStatus]
    overall_status: str  # 'healthy', 'degraded', 'offline'


class ModelListResponse(BaseModel):
    """Response model for model list."""
    models_by_provider: Dict[str, Any]


class TestExtractionRequest(BaseModel):
    """Request model for testing extraction."""
    raw_text: str = Field(..., min_length=10, description="Sample vulnerability text")
    provider: Optional[str] = Field(None, description="Override provider for test")
    model: Optional[str] = Field(None, description="Override model for test")


class TestExtractionResponse(BaseModel):
    """Response model for test extraction."""
    success: bool
    provider_used: Optional[str] = None
    extraction: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ProviderTemplateResponse(BaseModel):
    """Response model for provider configuration template."""
    provider: str
    description: str
    required_fields: List[str]
    optional_fields: List[str]
    example: Dict[str, Any]


# Helper functions
async def get_or_create_config(db: AsyncSession) -> LLMConfig:
    """Get existing LLM config or create default."""
    result = await db.execute(select(LLMConfig))
    config = result.scalar_one_or_none()

    if not config:
        config = LLMConfig(
            primary_provider="ollama",
            provider_config={
                "ollama": {"base_url": "http://localhost:11434"}
            }
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config


# Endpoints
@router.get("/config", response_model=LLMConfigResponse)
async def get_llm_config(db: AsyncSession = Depends(get_db)):
    """
    Get current LLM configuration.

    Returns multi-provider configuration including primary and fallback providers.
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

    Allows updating primary provider, fallback providers, and processing parameters.
    """
    config = await get_or_create_config(db)

    # Update primary provider
    if updates.primary_provider is not None:
        available = LLMProviderFactory.get_available_providers()
        if updates.primary_provider not in available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown provider: {updates.primary_provider}. Available: {available}"
            )
        config.primary_provider = updates.primary_provider

    # Update fallback providers
    if updates.fallback_providers is not None:
        available = LLMProviderFactory.get_available_providers()
        for provider in updates.fallback_providers:
            if provider not in available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown provider: {provider}. Available: {available}"
                )
        config.fallback_providers = ",".join(updates.fallback_providers)

    # Update provider-specific configs
    if updates.provider_config is not None:
        # Merge with existing config
        if not config.provider_config:
            config.provider_config = {}
        for provider_name, provider_cfg in updates.provider_config.items():
            config.provider_config[provider_name] = provider_cfg

    # Update other parameters
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


@router.get("/providers")
async def list_providers():
    """
    List available LLM providers and configuration templates.

    Shows all supported providers and what configuration is required for each.
    """
    available_providers = LLMProviderFactory.get_available_providers()

    providers_info = {}
    for provider_name in available_providers:
        template = LLMProviderManager.get_provider_config_template(provider_name)
        providers_info[provider_name] = template

    return {
        "available_providers": available_providers,
        "providers": providers_info,
    }


@router.get("/test", response_model=ProviderStatus)
async def test_connection(db: AsyncSession = Depends(get_db)):
    """
    Test connection to primary LLM provider.

    Attempts to connect to configured primary provider and retrieve server info.
    """
    config = await get_or_create_config(db)

    try:
        # Create primary provider
        provider_config = config.provider_config or {}
        primary_config = provider_config.get(config.primary_provider, {})

        provider = LLMProviderFactory.create_provider(
            config.primary_provider,
            **primary_config
        )

        result = await provider.test_connection()

        # Update config with test results
        from datetime import datetime
        config.last_connection_test = datetime.utcnow()
        config.connection_status = "connected"
        await db.commit()

        return ProviderStatus(
            provider=config.primary_provider,
            status="connected",
            message=f"Successfully connected to {config.primary_provider}",
            details=result
        )

    except Exception as e:
        config.connection_status = "failed"
        await db.commit()

        logger.error(f"Connection test failed for {config.primary_provider}: {e}")
        return ProviderStatus(
            provider=config.primary_provider,
            status="disconnected",
            message=str(e),
            details={"error": str(e)}
        )


@router.get("/test-all", response_model=MultiProviderStatus)
async def test_all_providers(db: AsyncSession = Depends(get_db)):
    """
    Test all configured providers (primary and fallbacks).

    Attempts to connect to each configured provider and reports status.
    """
    config = await get_or_create_config(db)

    # Test primary provider
    provider_config_dict = config.provider_config or {}

    async def test_provider(provider_name: str) -> ProviderStatus:
        try:
            provider_cfg = provider_config_dict.get(provider_name, {})
            provider = LLMProviderFactory.create_provider(
                provider_name,
                **provider_cfg
            )
            result = await provider.test_connection()
            return ProviderStatus(
                provider=provider_name,
                status="connected",
                message=f"Connected",
                details=result
            )
        except Exception as e:
            logger.warning(f"Failed to connect to {provider_name}: {e}")
            return ProviderStatus(
                provider=provider_name,
                status="disconnected",
                message=str(e),
            )

    # Test primary
    primary_status = await test_provider(config.primary_provider)

    # Test fallbacks
    fallback_names = [
        f.strip() for f in (config.fallback_providers or "").split(",") if f.strip()
    ]
    fallback_statuses = [
        await test_provider(name) for name in fallback_names
    ]

    # Determine overall status
    if primary_status.status == "connected":
        overall = "healthy"
    elif fallback_statuses and any(s.status == "connected" for s in fallback_statuses):
        overall = "degraded"
    else:
        overall = "offline"

    return MultiProviderStatus(
        primary=primary_status,
        fallbacks=fallback_statuses,
        overall_status=overall,
    )


@router.get("/models", response_model=ModelListResponse)
async def list_models(db: AsyncSession = Depends(get_db)):
    """
    List available models from all configured providers.

    Discovers models from primary and fallback providers.
    """
    config = await get_or_create_config(db)

    provider_config_dict = config.provider_config or {}
    models_by_provider = {}

    async def list_provider_models(provider_name: str) -> Dict[str, Any]:
        try:
            provider_cfg = provider_config_dict.get(provider_name, {})
            provider = LLMProviderFactory.create_provider(
                provider_name,
                **provider_cfg
            )
            models = await provider.list_models()
            return {
                "status": "connected",
                "models": models,
                "count": len(models),
            }
        except Exception as e:
            logger.warning(f"Failed to list models from {provider_name}: {e}")
            return {
                "status": "disconnected",
                "error": str(e),
                "models": [],
                "count": 0,
            }

    # Get models from primary and all fallbacks
    all_providers = [config.primary_provider]
    if config.fallback_providers:
        all_providers.extend([
            f.strip() for f in config.fallback_providers.split(",") if f.strip()
        ])

    for provider_name in all_providers:
        models_by_provider[provider_name] = await list_provider_models(provider_name)

    # Update available models in config
    all_models = []
    for provider_data in models_by_provider.values():
        if provider_data.get("models"):
            all_models.extend([m.get("name") for m in provider_data["models"]])

    config.available_models = {"all_available": all_models}
    await db.commit()

    return ModelListResponse(models_by_provider=models_by_provider)


@router.post("/test-extract", response_model=TestExtractionResponse)
async def test_extraction(
    request: TestExtractionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Test LLM extraction on sample text.

    Allows testing the multi-provider extraction pipeline with custom text.
    Uses primary provider by default, or override with specific provider.
    """
    config = await get_or_create_config(db)

    provider_name = request.provider or config.primary_provider
    model = request.model or config.selected_model

    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No model specified and no default model configured"
        )

    try:
        # Create provider and service
        provider_config_dict = config.provider_config or {}
        provider_cfg = provider_config_dict.get(provider_name, {})

        provider = LLMProviderFactory.create_provider(
            provider_name,
            **provider_cfg
        )

        # Check model availability
        if not await provider.check_model_available(model):
            available = await provider.list_models()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{model}' not available on {provider_name}. "
                        f"Available: {[m['name'] for m in available]}"
            )

        # Create service and extract
        from app.backend.services.llm_multi_provider_service import MultiProviderLLMService
        service = MultiProviderLLMService(
            primary_provider=provider,
            model=model,
            temperature=config.temperature,
            confidence_threshold=config.confidence_threshold,
        )

        result = await service.extract_vulnerability(request.raw_text)

        return TestExtractionResponse(
            success=True,
            provider_used=provider_name,
            extraction=result.to_dict(),
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test extraction failed: {e}")
        return TestExtractionResponse(
            success=False,
            provider_used=provider_name,
            extraction=None,
            error=str(e)
        )
