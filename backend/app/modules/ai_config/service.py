import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import (
    DEFAULT_OUTPUT_PREFERENCE,
    DEFAULT_RAG_CONFIG,
    DEFAULT_SCOPE_PREFERENCE,
    DEFAULT_TEAM_STANDARD,
)
from app.modules.ai_config.models import AiConfiguration
from app.modules.ai_config.schemas import AiConfigCreate, AiConfigUpdate

logger = logging.getLogger(__name__)


class AiConfigService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_config(self, config_id: UUID) -> AiConfiguration:
        config = await self.session.get(AiConfiguration, config_id)
        if not config or config.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found")
        return config

    async def get_by_scope(self, scope: str, scope_id: UUID | None = None) -> AiConfiguration | None:
        query = select(AiConfiguration).where(
            AiConfiguration.scope == scope,
            AiConfiguration.deleted_at.is_(None),
        )
        if scope_id:
            query = query.where(AiConfiguration.scope_id == scope_id)
        else:
            query = query.where(AiConfiguration.scope_id.is_(None))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_config(self, data: AiConfigCreate) -> AiConfiguration:
        config = AiConfiguration(**data.model_dump(exclude_none=True))
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def update_config(self, config_id: UUID, data: AiConfigUpdate) -> AiConfiguration:
        config = await self.get_config(config_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(config, key, value)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def get_effective_config(self, iteration_id: UUID | None = None, product_id: UUID | None = None) -> dict:
        """Get merged config following inheritance: iteration > product > global > default."""
        merged: dict = {
            "team_standard_prompt": DEFAULT_TEAM_STANDARD,
            "output_preference": dict(DEFAULT_OUTPUT_PREFERENCE),
            "scope_preference": dict(DEFAULT_SCOPE_PREFERENCE),
            "rag_config": dict(DEFAULT_RAG_CONFIG),
            "module_rules": {},
            "custom_checklist": [],
            "llm_model": None,
            "llm_temperature": None,
        }

        global_config = await self.get_by_scope("global")
        if global_config:
            merged = self._merge_config(merged, global_config)

        if product_id:
            product_config = await self.get_by_scope("product", product_id)
            if product_config:
                merged = self._merge_config(merged, product_config)

        if iteration_id:
            iteration_config = await self.get_by_scope("iteration", iteration_id)
            if iteration_config:
                merged = self._merge_config(merged, iteration_config)

        return merged

    def _merge_config(self, base: dict, override: AiConfiguration) -> dict:
        """Merge override config into base. Text fields override, JSONB deep merge."""
        result = dict(base)

        if override.team_standard_prompt:
            result["team_standard_prompt"] = override.team_standard_prompt
        if override.llm_model:
            result["llm_model"] = override.llm_model
        if override.llm_temperature is not None:
            result["llm_temperature"] = override.llm_temperature

        if override.output_preference:
            result["output_preference"] = {**result.get("output_preference", {}), **override.output_preference}
        if override.scope_preference:
            result["scope_preference"] = {**result.get("scope_preference", {}), **override.scope_preference}
        if override.rag_config:
            result["rag_config"] = {**result.get("rag_config", {}), **override.rag_config}
        if override.module_rules:
            result["module_rules"] = {**result.get("module_rules", {}), **override.module_rules}
        if override.custom_checklist:
            existing = result.get("custom_checklist", [])
            if isinstance(existing, list) and isinstance(override.custom_checklist, list):
                result["custom_checklist"] = existing + override.custom_checklist
            else:
                result["custom_checklist"] = override.custom_checklist

        return result

    async def list_configs(self) -> list[AiConfiguration]:
        result = await self.session.execute(select(AiConfiguration).where(AiConfiguration.deleted_at.is_(None)))
        return list(result.scalars().all())
