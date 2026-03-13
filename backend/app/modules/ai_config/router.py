import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.ai.prompts import _MODULE_PROMPTS, get_system_prompt
from app.core.dependencies import AsyncSessionDep
from app.modules.ai_config.schemas import (
    AiConfigCreate,
    AiConfigResponse,
    AiConfigUpdate,
    ModelConfigCreate,
    ModelConfigResponse,
    ModelConfigUpdate,
    PromptConfigResponse,
    PromptConfigUpdate,
    PromptHistoryResponse,
)
from app.modules.ai_config.service import AiConfigService, ModelConfigService, PromptConfigService

router = APIRouter(prefix="/ai-config", tags=["ai-config"])


# ── Legacy scope-based config endpoints ────────────────────────────


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


@router.get("/providers")
async def get_providers() -> dict:
    """返回平台支持的 LLM 提供商和各提供商的模型版本列表。"""
    return {
        "providers": [
            {
                "id": "zhipu",
                "name": "智谱AI",
                "description": "国内领先大模型，中文理解强，响应速度快",
                "api_key_placeholder": "xxxxxxxx.xxxxxxxxxx",
                "models": [
                    {
                        "id": "glm-5",
                        "name": "GLM-5",
                        "description": "能力最强，稳定性最高，适合复杂用例生成",
                        "recommended": True,
                    },
                    {
                        "id": "glm-4-flash",
                        "name": "GLM-4-Flash",
                        "description": "速度最快，适合实时对话",
                    },
                    {"id": "glm-4", "name": "GLM-4", "description": "综合能力强，性价比高"},
                    {"id": "glm-4-air", "name": "GLM-4-Air", "description": "轻量版，低延迟"},
                    {"id": "glm-4-airx", "name": "GLM-4-AirX", "description": "极速推理版"},
                    {"id": "glm-4-long", "name": "GLM-4-Long", "description": "超长上下文（128K）"},
                ],
            },
            {
                "id": "dashscope",
                "name": "阿里云百炼",
                "description": "推理能力强，结构化输出稳定，适合复杂用例生成",
                "api_key_placeholder": "sk-xxxxxxxxxxxxxxxx",
                "models": [
                    {
                        "id": "qwen-max",
                        "name": "Qwen-Max",
                        "description": "最高质量，复杂推理首选",
                        "recommended": True,
                    },
                    {"id": "qwen-plus", "name": "Qwen-Plus", "description": "质量与速度均衡"},
                    {"id": "qwen-turbo", "name": "Qwen-Turbo", "description": "高速低成本"},
                    {"id": "qwen-long", "name": "Qwen-Long", "description": "超长上下文（1M Token）"},
                ],
            },
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "description": "DeepSeek 系列模型，推理和编程能力出色",
                "api_key_placeholder": "sk-xxxxxxxxxxxxxxxx",
                "models": [
                    {"id": "deepseek-chat", "name": "DeepSeek-V3", "description": "通用对话模型", "recommended": True},
                    {"id": "deepseek-reasoner", "name": "DeepSeek-R1", "description": "深度推理模型"},
                ],
            },
            {
                "id": "moonshot",
                "name": "Kimi (月之暗面)",
                "description": "超长上下文，中文理解优秀",
                "api_key_placeholder": "sk-xxxxxxxxxxxxxxxx",
                "models": [
                    {"id": "moonshot-v1-8k", "name": "Moonshot-v1-8K", "description": "标准版"},
                    {
                        "id": "moonshot-v1-32k",
                        "name": "Moonshot-v1-32K",
                        "description": "长上下文",
                        "recommended": True,
                    },
                    {"id": "moonshot-v1-128k", "name": "Moonshot-v1-128K", "description": "超长上下文"},
                ],
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "兼容 OpenAI 协议的模型",
                "api_key_placeholder": "sk-xxxxxxxxxxxxxxxx",
                "models": [
                    {"id": "gpt-4o", "name": "GPT-4o", "description": "多模态旗舰模型", "recommended": True},
                    {"id": "gpt-4o-mini", "name": "GPT-4o mini", "description": "低成本版"},
                    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "强推理，128K 上下文"},
                ],
            },
            {
                "id": "ollama",
                "name": "Ollama (本地)",
                "description": "本地部署开源模型，无需 API Key",
                "api_key_placeholder": "（留空即可）",
                "requires_base_url": True,
                "default_base_url": "http://localhost:11434",
                "models": [
                    {"id": "llama3", "name": "Llama 3", "description": "Meta 开源旗舰模型", "recommended": True},
                    {"id": "qwen2", "name": "Qwen 2", "description": "通义千问开源版"},
                    {"id": "deepseek-coder", "name": "DeepSeek Coder", "description": "编程优化模型"},
                ],
            },
            {
                "id": "custom",
                "name": "自定义 (OpenAI 兼容)",
                "description": "任何兼容 OpenAI API 协议的服务",
                "api_key_placeholder": "your-api-key",
                "requires_base_url": True,
                "default_base_url": "https://your-api.example.com/v1",
                "models": [],
            },
        ]
    }


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
        import httpx

        from app.core.config import settings

        async with httpx.AsyncClient(trust_env=False, timeout=5) as client:
            r = await client.get(f"{settings.qdrant_url}/collections")
            r.raise_for_status()
            data = r.json()
        collections = data.get("result", {}).get("collections", [])
        return {
            "status": "ok",
            "qdrant_url": settings.qdrant_url,
            "collections_count": len(collections),
            "collection_names": [c["name"] for c in collections],
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


# ── Model Configuration CRUD endpoints ────────────────────────────


@router.get("/models/list", response_model=list[ModelConfigResponse])
async def list_model_configs(session: AsyncSessionDep) -> list[ModelConfigResponse]:
    svc = ModelConfigService(session)
    items = await svc.list_models()
    return [ModelConfigResponse.model_validate(svc.serialize(m)) for m in items]


@router.post("/models", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_model_config(data: ModelConfigCreate, session: AsyncSessionDep) -> ModelConfigResponse:
    svc = ModelConfigService(session)
    item = await svc.create_model(data)
    return ModelConfigResponse.model_validate(svc.serialize(item))


@router.patch("/models/{model_config_id}", response_model=ModelConfigResponse)
async def update_model_config(
    model_config_id: uuid.UUID, data: ModelConfigUpdate, session: AsyncSessionDep
) -> ModelConfigResponse:
    svc = ModelConfigService(session)
    item = await svc.update_model(model_config_id, data)
    return ModelConfigResponse.model_validate(svc.serialize(item))


@router.delete("/models/{model_config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_config(model_config_id: uuid.UUID, session: AsyncSessionDep) -> None:
    svc = ModelConfigService(session)
    await svc.delete_model(model_config_id)


@router.post("/models/{model_config_id}/test")
async def test_model_config(model_config_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    """Test connection for a specific model configuration."""
    svc = ModelConfigService(session)
    item = await svc.get_model(model_config_id)
    try:
        from app.ai.llm_client import invoke_llm

        result = await invoke_llm(
            [{"role": "user", "content": "请回复'连接成功'四个字。"}],
            provider=item.provider,
            max_retries=0,
        )
        return {
            "status": "ok",
            "model": item.model_id,
            "response_preview": result.content[:100],
        }
    except Exception as e:
        return {
            "status": "error",
            "model": item.model_id,
            "error": str(e),
        }


# ── Prompt Configuration endpoints ────────────────────────────────


@router.get("/prompts")
async def list_prompt_configs(session: AsyncSessionDep) -> list[dict]:
    """Return all 6 module prompts, merging DB records with hardcoded defaults."""
    svc = PromptConfigService(session)
    db_records = await svc.list_prompts()
    db_map = {r.module: r for r in db_records}

    result = []
    for module_key in _MODULE_PROMPTS:
        if module_key in db_map:
            r = db_map[module_key]
            result.append({
                "id": str(r.id),
                "module_key": r.module,
                "prompt_text": r.system_prompt,
                "is_default": False,
                "is_customized": r.is_customized,
                "version": r.version,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        else:
            result.append({
                "id": None,
                "module_key": module_key,
                "prompt_text": get_system_prompt(module_key),
                "is_default": True,
                "is_customized": False,
                "version": 0,
                "updated_at": None,
                "created_at": None,
            })
    return result


@router.get("/prompts/{module}", response_model=PromptConfigResponse | None)
async def get_prompt_config(module: str, session: AsyncSessionDep) -> PromptConfigResponse | None:
    svc = PromptConfigService(session)
    item = await svc.get_prompt(module)
    if not item:
        return None
    return PromptConfigResponse.model_validate(item)


@router.put("/prompts/{module}", response_model=PromptConfigResponse)
async def upsert_prompt_config(module: str, data: PromptConfigUpdate, session: AsyncSessionDep) -> PromptConfigResponse:
    svc = PromptConfigService(session)
    item = await svc.upsert_prompt(module, data.system_prompt, data.change_reason)
    return PromptConfigResponse.model_validate(item)


@router.delete("/prompts/{module}", status_code=status.HTTP_204_NO_CONTENT)
async def reset_prompt_config(module: str, session: AsyncSessionDep) -> None:
    """Reset module prompt to system default by soft-deleting the custom config."""
    svc = PromptConfigService(session)
    await svc.reset_prompt(module)


@router.get("/prompts/{module}/history", response_model=list[PromptHistoryResponse])
async def get_prompt_history(module: str, session: AsyncSessionDep) -> list[PromptHistoryResponse]:
    svc = PromptConfigService(session)
    items = await svc.get_history(module)
    return [PromptHistoryResponse.model_validate(h) for h in items]
