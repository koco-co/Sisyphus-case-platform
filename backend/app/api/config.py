"""
LLM configuration management API.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.llm_config import LLMConfig


router = APIRouter(prefix="/api/config", tags=["config"])


# Pydantic models
class LLMConfigSchema(BaseModel):
    """Schema for LLM configuration input/output."""
    provider: str = "openai"
    api_key: str = ""
    model: str = "gpt-4"


class LLMConfigResponse(BaseModel):
    """Response schema for LLM configuration."""
    provider: str
    api_key: str
    model: str


# Valid providers and their models
PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    },
    "zhipu": {
        "name": "智谱 AI (GLM)",
        "models": ["glm-4", "glm-4-plus", "glm-3-turbo"]
    },
    "alibaba": {
        "name": "阿里百炼",
        "models": ["qwen-turbo", "qwen-plus", "qwen-max"]
    },
    "minimax": {
        "name": "MiniMax",
        "models": ["abab5.5-chat", "abab5.5s-chat"]
    }
}


@router.get("/llm", response_model=LLMConfigResponse)
async def get_llm_config(db: AsyncSession = Depends(get_db)):
    """Get the active LLM configuration."""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.is_active == True).limit(1)
    )
    config = result.scalar_one_or_none()

    if not config:
        # Create default configuration
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            is_active=True,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return {
        "provider": config.provider,
        "api_key": "",  # Don't return actual API key
        "model": config.model,
    }


@router.put("/llm", response_model=LLMConfigResponse)
async def update_llm_config(
    data: LLMConfigSchema,
    db: AsyncSession = Depends(get_db),
):
    """Update the active LLM configuration."""
    # Validate provider
    if data.provider not in PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Must be one of: {', '.join(PROVIDERS.keys())}"
        )

    # Validate model for the provider
    if data.model not in PROVIDERS[data.provider]["models"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model for {data.provider}. Must be one of: {', '.join(PROVIDERS[data.provider]['models'])}"
        )

    result = await db.execute(
        select(LLMConfig).where(LLMConfig.is_active == True).limit(1)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = LLMConfig(
            provider=data.provider,
            model=data.model,
            is_active=True,
        )
        db.add(config)
    else:
        config.provider = data.provider
        config.model = data.model
        # Only update API key if a new one is provided
        if data.api_key:
            config.api_key_encrypted = data.api_key  # TODO: Implement actual encryption

    await db.commit()
    await db.refresh(config)

    return {
        "provider": config.provider,
        "api_key": "",
        "model": config.model,
    }


@router.get("/providers")
async def get_providers():
    """Get available LLM providers and their models."""
    return PROVIDERS
