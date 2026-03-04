"""
User configuration management API.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user_config import UserConfig


router = APIRouter(prefix="/api/configs", tags=["configs"])


# Pydantic models
class ConfigCreate(BaseModel):
    provider: str
    api_key_encrypted: str
    generator_model: Optional[str] = None
    reviewer_model: Optional[str] = None


class ConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    api_key_encrypted: str
    generator_model: Optional[str]
    reviewer_model: Optional[str]
    is_active: bool
    created_at: datetime


class ActivateResponse(BaseModel):
    message: str


# Valid providers
VALID_PROVIDERS = {"glm", "minimax", "alibaba"}


@router.post("/", response_model=ConfigResponse, status_code=201)
async def create_config(
    config: ConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new configuration."""
    # Validate provider
    if config.provider not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Must be one of: {', '.join(VALID_PROVIDERS)}"
        )

    # Create new config
    db_config = UserConfig(
        provider=config.provider,
        api_key_encrypted=config.api_key_encrypted,
        generator_model=config.generator_model,
        reviewer_model=config.reviewer_model,
        is_active=False  # New configs are inactive by default
    )
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)

    return db_config


@router.get("/", response_model=List[ConfigResponse])
async def list_configs(db: AsyncSession = Depends(get_db)):
    """Get all configurations."""
    result = await db.execute(select(UserConfig))
    configs = result.scalars().all()
    return configs


@router.get("/active", response_model=ConfigResponse)
async def get_active_config(db: AsyncSession = Depends(get_db)):
    """Get the currently active configuration."""
    result = await db.execute(
        select(UserConfig).where(UserConfig.is_active == True)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="No active configuration found"
        )

    return config


@router.patch("/{config_id}/activate", response_model=ActivateResponse)
async def activate_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Activate a specific configuration (deactivates all others)."""
    # Check if config exists
    result = await db.execute(select(UserConfig).where(UserConfig.id == config_id))
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Configuration not found"
        )

    # Deactivate all configs
    await db.execute(
        update(UserConfig).values(is_active=False)
    )

    # Activate the specified config
    config.is_active = True
    await db.commit()

    return ActivateResponse(message="Configuration activated")
