"""向量嵌入器 — 将文本转换为向量表示。

支持多种嵌入模型后端：
- dashscope (通义千问 text-embedding-v3)
- zhipu (智谱 embedding-3)
- openai (text-embedding-3-small)

通过 ``app.core.config.settings`` 读取 provider 和 API Key，
自动选择对应的嵌入后端。
"""

import logging
from typing import TYPE_CHECKING

import httpx

from app.core.config import settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 嵌入维度常量
# ═══════════════════════════════════════════════════════════════════

_DIMENSIONS: dict[str, int] = {
    "dashscope": 1024,
    "zhipu": 2048,
    "openai": 1536,
}

EMBEDDING_DIMENSION: int = _DIMENSIONS.get(settings.llm_provider, 1024)

# ═══════════════════════════════════════════════════════════════════
# 嵌入 API 调用
# ═══════════════════════════════════════════════════════════════════

_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


async def embed_texts(texts: list[str], *, batch_size: int = 16) -> list[list[float]]:
    """批量嵌入文本，返回与输入等长的向量列表。

    Args:
        texts: 待嵌入的文本列表。
        batch_size: 每次 API 调用的批大小（避免超限）。

    Returns:
        二维列表 ``[[float, ...], ...]``，长度与 texts 相同。
    """
    if not texts:
        return []

    provider = settings.llm_provider
    all_vectors: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        vectors = await _embed_batch(batch, provider)
        all_vectors.extend(vectors)

    if len(all_vectors) != len(texts):
        raise ValueError(f"嵌入结果数量不匹配: 输入 {len(texts)}, 返回 {len(all_vectors)}")

    logger.info("嵌入完成: %d 条文本 (provider=%s)", len(texts), provider)
    return all_vectors


async def embed_query(text: str) -> list[float]:
    """对单条查询文本进行嵌入。"""
    vectors = await embed_texts([text])
    return vectors[0]


# ═══════════════════════════════════════════════════════════════════
# Provider 实现
# ═══════════════════════════════════════════════════════════════════


async def _embed_batch(texts: list[str], provider: str) -> list[list[float]]:
    if provider == "dashscope":
        return await _embed_dashscope(texts)
    if provider == "zhipu":
        return await _embed_zhipu(texts)
    if provider == "openai":
        return await _embed_openai(texts)
    raise ValueError(f"不支持的嵌入 provider: {provider}")


async def _embed_dashscope(texts: list[str]) -> list[list[float]]:
    """通义千问 text-embedding-v3。"""
    url = f"{settings.dashscope_base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "text-embedding-v3",
        "input": texts,
        "dimensions": _DIMENSIONS["dashscope"],
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]


async def _embed_zhipu(texts: list[str]) -> list[list[float]]:
    """智谱 embedding-3。"""
    from zhipuai import ZhipuAI

    client = ZhipuAI(
        api_key=settings.zhipu_api_key,
        http_client=httpx.Client(proxy=None, trust_env=False),
    )

    vectors: list[list[float]] = []
    for text in texts:
        resp = client.embeddings.create(model="embedding-3", input=text)
        vectors.append(resp.data[0].embedding)

    return vectors


async def _embed_openai(texts: list[str]) -> list[list[float]]:
    """OpenAI text-embedding-3-small。"""
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "text-embedding-3-small",
        "input": texts,
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
