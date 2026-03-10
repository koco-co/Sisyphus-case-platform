"""非流式 LLM 调用客户端 — 与 stream_adapter 共享 provider 配置。"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, cast

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    """LLM 调用结果。"""

    content: str
    usage: dict = field(default_factory=dict)


async def invoke_llm(
    messages: list[dict],
    *,
    provider: str | None = None,
    max_retries: int = 2,
) -> LLMResult:
    """非流式调用 LLM，带重试和降级。

    1. 尝试主模型，重试 max_retries 次（指数退避）
    2. 降级到备用模型
    """
    primary = (provider or settings.llm_provider).lower()
    fallback = getattr(settings, "llm_fallback_provider", "zhipu").lower()

    providers_to_try = [primary]
    if fallback and fallback != primary:
        providers_to_try.append(fallback)

    last_error: Exception | None = None

    for provider_name in providers_to_try:
        for attempt in range(max_retries + 1):
            try:
                return await _invoke(provider_name, messages)
            except Exception as e:
                last_error = e
                logger.warning("LLM %s attempt %d failed: %s", provider_name, attempt + 1, e)
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)

    raise RuntimeError(f"所有 LLM 提供商调用失败: {last_error}")


async def _invoke(provider: str, messages: list[dict]) -> LLMResult:
    if provider == "zhipu":
        return await _invoke_zhipu(messages)
    if provider == "dashscope":
        return await _invoke_dashscope(messages)
    return await _invoke_openai(messages)


def _extract_usage(usage: object | None) -> dict:
    if not usage:
        return {}
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
        "completion_tokens": getattr(usage, "completion_tokens", 0),
    }


async def _invoke_openai(messages: list[dict]) -> LLMResult:
    import httpx
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        http_client=httpx.AsyncClient(proxy=None, trust_env=False),
    )
    response = cast(
        Any,
        await client.chat.completions.create(
        model=settings.openai_model,
            messages=cast(Any, messages),
        ),
    )
    return LLMResult(
        content=response.choices[0].message.content or "",
        usage=_extract_usage(response.usage),
    )


async def _invoke_zhipu(messages: list[dict]) -> LLMResult:
    import httpx
    from zhipuai import ZhipuAI

    client = ZhipuAI(
        api_key=settings.zhipu_api_key,
        http_client=httpx.Client(proxy=None, trust_env=False),
    )

    def _call():
        return client.chat.completions.create(model=settings.zhipu_model, messages=cast(Any, messages))

    response = cast(Any, await asyncio.to_thread(_call))
    return LLMResult(
        content=response.choices[0].message.content or "",
        usage=_extract_usage(response.usage),
    )


async def _invoke_dashscope(messages: list[dict]) -> LLMResult:
    import httpx
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        http_client=httpx.AsyncClient(proxy=None, trust_env=False),
    )
    response = cast(
        Any,
        await client.chat.completions.create(
        model=settings.dashscope_model,
            messages=cast(Any, messages),
        ),
    )
    return LLMResult(
        content=response.choices[0].message.content or "",
        usage=_extract_usage(response.usage),
    )
