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


@router.post("/test-llm")
async def test_llm_connection(
    provider: str = "zhipu",
    model: str | None = None,
) -> dict:
    """Test LLM provider connection by sending a simple ping message."""
    try:
        from app.ai.llm_client import invoke_llm

        result = await invoke_llm(
            [{"role": "user", "content": "请回复'连接成功'四个字。"}],
            provider=provider,
            max_retries=0,
        )
        return {
            "status": "ok",
            "provider": provider,
            "response_preview": result.content[:100],
            "usage": result.usage,
        }
    except Exception as e:
        return {
            "status": "error",
            "provider": provider,
            "error": str(e),
        }


@router.post("/test-embedding")
async def test_embedding_connection() -> dict:
    """Test embedding/vector service connection."""
    try:
        from qdrant_client import QdrantClient

        from app.core.config import settings

        client = QdrantClient(url=settings.qdrant_url, timeout=5)
        collections = client.get_collections()
        return {
            "status": "ok",
            "qdrant_url": settings.qdrant_url,
            "collections_count": len(collections.collections),
            "collection_names": [c.name for c in collections.collections],
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }
