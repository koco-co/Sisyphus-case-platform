import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.dependencies import AsyncSessionDep
from app.modules.ai_config.schemas import AiConfigCreate, AiConfigResponse, AiConfigUpdate
from app.modules.ai_config.service import AiConfigService

router = APIRouter(prefix="/ai-config", tags=["ai-config"])


@router.get("", response_model=list[AiConfigResponse])
async def list_configs(session: AsyncSessionDep) -> list[AiConfigResponse]:
    service = AiConfigService(session)
    configs = await service.list_configs()
    return [AiConfigResponse.model_validate(c) for c in configs]


@router.get("/effective", response_model=dict)
async def get_effective_config(
    session: AsyncSessionDep,
    iteration_id: Annotated[uuid.UUID | None, Query()] = None,
    product_id: Annotated[uuid.UUID | None, Query()] = None,
) -> dict:
    service = AiConfigService(session)
    return await service.get_effective_config(iteration_id, product_id)


@router.get("/{config_id}", response_model=AiConfigResponse)
async def get_config(config_id: uuid.UUID, session: AsyncSessionDep) -> AiConfigResponse:
    service = AiConfigService(session)
    config = await service.get_config(config_id)
    return AiConfigResponse.model_validate(config)


@router.post("", response_model=AiConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(data: AiConfigCreate, session: AsyncSessionDep) -> AiConfigResponse:
    service = AiConfigService(session)
    config = await service.create_config(data)
    return AiConfigResponse.model_validate(config)


@router.patch("/{config_id}", response_model=AiConfigResponse)
async def update_config(config_id: uuid.UUID, data: AiConfigUpdate, session: AsyncSessionDep) -> AiConfigResponse:
    service = AiConfigService(session)
    config = await service.update_config(config_id, data)
    return AiConfigResponse.model_validate(config)
