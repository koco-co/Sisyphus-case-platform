"""统一的流式输出适配器，支持 OpenAI / Anthropic / ZhiPu。

SSE 事件格式：
  event: thinking\ndata: {"delta": "..."}\n\n
  event: content\ndata: {"delta": "..."}\n\n
  event: done\ndata: {"usage": {...}}\n\n

性能优化：
  - 心跳机制：每 15s 发送 :keepalive 注释行
  - 超时保护：5 分钟无输出自动关闭
"""

import asyncio
import importlib
import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any, cast

from app.core.config import settings

logger = logging.getLogger(__name__)

# 心跳间隔 (秒) 和超时时间 (秒)
_HEARTBEAT_INTERVAL = 15
_STREAM_TIMEOUT = 300  # 5 分钟


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _keepalive() -> str:
    return ": keepalive\n\n"


async def openai_thinking_stream(
    messages: list[dict],
    system: str = "",
) -> AsyncIterator[str]:
    """OpenAI 流式输出。"""
    import httpx
    from openai import AsyncOpenAI

    no_proxy_client = httpx.AsyncClient(proxy=None, trust_env=False)
    client = AsyncOpenAI(api_key=settings.openai_api_key, http_client=no_proxy_client)

    yield _sse("thinking", {"delta": "正在分析需求，梳理测试场景...\n"})

    all_messages = messages
    if system:
        all_messages = [{"role": "system", "content": system}, *messages]

    stream = cast(
        Any,
        await client.chat.completions.create(
        model=settings.openai_model,
            messages=cast(Any, all_messages),
            stream=True,
        ),
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield _sse("content", {"delta": delta})

    yield _sse("done", {"usage": {}})


async def anthropic_thinking_stream(
    messages: list[dict],
    system: str = "",
) -> AsyncIterator[str]:
    """Claude 扩展思考流式输出。"""
    anthropic = importlib.import_module("anthropic")

    client = anthropic.AsyncAnthropic()

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        thinking={"type": "enabled", "budget_tokens": 10000},
        system=system,
        messages=cast(Any, messages),
    ) as stream:
        async for event in stream:
            if event.type == "content_block_delta":
                if event.delta.type == "thinking_delta":
                    yield _sse("thinking", {"delta": event.delta.thinking})
                elif event.delta.type == "text_delta":
                    yield _sse("content", {"delta": event.delta.text})

    yield _sse("done", {"usage": {}})


async def zhipu_thinking_stream(
    messages: list[dict],
    system: str = "",
) -> AsyncIterator[str]:
    """智谱 GLM 流式输出，运行在线程池以避免阻塞事件循环。"""
    import httpx
    from zhipuai import ZhipuAI

    # 绕过系统 SOCKS 代理，ZhiPu 是国内服务无需代理
    no_proxy_client = httpx.Client(proxy=None, trust_env=False)
    client = ZhipuAI(api_key=settings.zhipu_api_key, http_client=no_proxy_client)

    yield _sse("thinking", {"delta": "正在分析需求，梳理测试场景...\n"})

    all_messages = messages
    if system:
        all_messages = [{"role": "system", "content": system}, *messages]

    # ZhiPu SDK 是同步的，放到线程池中执行
    def _create_stream():
        return client.chat.completions.create(
            model=settings.zhipu_model,
            messages=cast(Any, all_messages),
            stream=True,
        )

    stream = await asyncio.to_thread(_create_stream)

    # 逐 chunk 消费也需要包在 to_thread 里
    def _next_chunk(iterator):
        try:
            return next(iterator)
        except StopIteration:
            return None

    while True:
        chunk = await asyncio.to_thread(_next_chunk, stream)
        if chunk is None:
            break
        choice = chunk.choices[0] if chunk.choices else None
        if choice and choice.delta and choice.delta.content:
            yield _sse("content", {"delta": choice.delta.content})

    yield _sse("done", {"usage": {}})


async def dashscope_thinking_stream(
    messages: list[dict],
    system: str = "",
) -> AsyncIterator[str]:
    """阿里百炼 Dashscope 流式输出 (OpenAI 兼容模式)。"""
    import httpx
    from openai import AsyncOpenAI

    # 绕过系统 SOCKS 代理，Dashscope 是国内服务无需代理
    no_proxy_client = httpx.AsyncClient(proxy=None, trust_env=False)
    client = AsyncOpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        http_client=no_proxy_client,
    )

    yield _sse("thinking", {"delta": "正在分析需求，梳理测试场景...\n"})

    all_messages = messages
    if system:
        all_messages = [{"role": "system", "content": system}, *messages]

    stream = cast(
        Any,
        await client.chat.completions.create(
        model=settings.dashscope_model,
            messages=cast(Any, all_messages),
            stream=True,
        ),
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield _sse("content", {"delta": chunk.choices[0].delta.content})

    yield _sse("done", {"usage": {}})


async def get_thinking_stream(
    messages: list[dict],
    system: str = "",
) -> AsyncIterator[str]:
    """根据 settings.llm_provider 选择适配器。"""
    provider = settings.llm_provider.lower()
    if provider == "anthropic":
        return anthropic_thinking_stream(messages, system)
    if provider == "zhipu":
        return zhipu_thinking_stream(messages, system)
    if provider == "dashscope":
        return dashscope_thinking_stream(messages, system)
    return openai_thinking_stream(messages, system)


_PROVIDER_FUNCS = {
    "openai": openai_thinking_stream,
    "anthropic": anthropic_thinking_stream,
    "zhipu": zhipu_thinking_stream,
    "dashscope": dashscope_thinking_stream,
}


async def _with_heartbeat_and_timeout(
    source: AsyncIterator[str],
) -> AsyncIterator[str]:
    """为任意 SSE 流添加心跳 (15s) 和超时保护 (5min)。"""
    last_activity = time.monotonic()

    async def _next_chunk():
        return await source.__anext__()

    while True:
        remaining = _STREAM_TIMEOUT - (time.monotonic() - last_activity)
        if remaining <= 0:
            logger.warning("SSE 流超时 (%ds 无输出)，自动关闭", _STREAM_TIMEOUT)
            yield _sse("content", {"delta": "\n\n⚠️ 流式输出超时，已自动关闭。"})
            yield _sse("done", {"usage": {}})
            return

        try:
            chunk = await asyncio.wait_for(
                _next_chunk(),
                timeout=min(_HEARTBEAT_INTERVAL, remaining),
            )
            last_activity = time.monotonic()
            yield chunk
        except TimeoutError:
            yield _keepalive()
        except StopAsyncIteration:
            return


async def get_thinking_stream_with_fallback(
    messages: list[dict],
    system: str = "",
    max_retries: int = 2,
) -> AsyncIterator[str]:
    """带重试、降级、心跳和超时保护的流式输出。

    1. 尝试主模型 (settings.llm_provider)
    2. 重试 max_retries 次（指数退避 1s, 2s）
    3. 降级到备用模型 (settings.llm_fallback_provider)
    4. 每 15s 发送 :keepalive，5min 无输出自动关闭
    """
    primary = settings.llm_provider.lower()
    fallback = getattr(settings, "llm_fallback_provider", "zhipu").lower()

    providers_to_try = [primary]
    if fallback and fallback != primary:
        providers_to_try.append(fallback)

    async def _stream_with_fallback() -> AsyncIterator[str]:
        for provider_name in providers_to_try:
            func = _PROVIDER_FUNCS.get(provider_name)
            if not func:
                continue
            for attempt in range(max_retries + 1):
                try:
                    raw_stream = func(messages, system)
                    guarded = _with_heartbeat_and_timeout(raw_stream)
                    has_content = False
                    async for chunk in guarded:
                        has_content = True
                        yield chunk
                    if has_content:
                        return
                except Exception as e:
                    logger.warning(
                        "LLM %s attempt %d failed: %s",
                        provider_name,
                        attempt + 1,
                        e,
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(2**attempt)

        # All providers failed
        yield _sse("content", {"delta": "⚠️ AI 服务暂时不可用，请稍后重试。"})
        yield _sse("done", {"usage": {}})

    return _stream_with_fallback()
