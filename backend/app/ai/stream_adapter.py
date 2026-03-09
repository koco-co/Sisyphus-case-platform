"""统一的流式输出适配器，支持 OpenAI / Anthropic / ZhiPu。

SSE 事件格式：
  event: thinking\ndata: {"delta": "..."}\n\n
  event: content\ndata: {"delta": "..."}\n\n
  event: done\ndata: {"usage": {...}}\n\n
"""

import asyncio
import json
from collections.abc import AsyncIterator

from app.core.config import settings


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


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

    stream = await client.chat.completions.create(
        model=settings.openai_model,
        messages=all_messages,
        stream=True,
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
    import anthropic

    client = anthropic.AsyncAnthropic()

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        thinking={"type": "enabled", "budget_tokens": 10000},
        system=system,
        messages=messages,
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
            messages=all_messages,
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

    stream = await client.chat.completions.create(
        model=settings.dashscope_model,
        messages=all_messages,
        stream=True,
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
