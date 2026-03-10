"""向量检索器 — 从 Qdrant 检索相似文档片段。

职责：
- 管理 Qdrant collection 的创建/连接
- 文档分块 → 嵌入 → 入库
- 语义检索 + 元数据过滤
- 格式化检索结果为 RAG 上下文字符串
"""

import logging
import uuid
from dataclasses import dataclass

from qdrant_client import QdrantClient, models

from app.core.config import settings
from app.engine.rag.chunker import Chunk
from app.engine.rag.embedder import EMBEDDING_DIMENSION, embed_query, embed_texts

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════════

COLLECTION_NAME = "knowledge_chunks"


# ═══════════════════════════════════════════════════════════════════
# 检索结果
# ═══════════════════════════════════════════════════════════════════


@dataclass
class RetrievalResult:
    """单条检索结果。"""

    content: str
    score: float
    metadata: dict
    chunk_id: str


# ═══════════════════════════════════════════════════════════════════
# Qdrant 客户端（延迟初始化）
# ═══════════════════════════════════════════════════════════════════

_client: QdrantClient | None = None


def _get_client() -> QdrantClient:
    """懒加载 Qdrant 客户端，避免导入时连接。"""
    global _client  # noqa: PLW0603
    if _client is None:
        _client = QdrantClient(
            url=settings.qdrant_url,
            timeout=30,
            trust_env=False,
        )
        logger.info("Qdrant 客户端已连接: %s", settings.qdrant_url)
    return _client


def ensure_collection() -> None:
    """确保 Qdrant collection 存在，不存在则创建。"""
    client = _get_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=models.Distance.COSINE,
            ),
        )
        logger.info(
            "创建 Qdrant collection: %s (dim=%d)",
            COLLECTION_NAME,
            EMBEDDING_DIMENSION,
        )


# ═══════════════════════════════════════════════════════════════════
# 文档入库
# ═══════════════════════════════════════════════════════════════════


async def index_chunks(chunks: list[Chunk], *, doc_id: str = "") -> int:
    """将分块嵌入并写入 Qdrant。

    Args:
        chunks: 分块列表。
        doc_id: 关联的知识库文档 ID（便于按文档删除）。

    Returns:
        成功写入的数量。
    """
    if not chunks:
        return 0

    ensure_collection()
    client = _get_client()

    texts = [c.content for c in chunks]
    vectors = await embed_texts(texts)

    points: list[models.PointStruct] = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        payload = {
            "content": chunk.content,
            "doc_id": doc_id or chunk.metadata.get("source_id", ""),
            "section_path": chunk.metadata.get("section_path", ""),
            "headers": chunk.metadata.get("headers", []),
            "chunk_index": chunk.index,
        }
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload,
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info("入库完成: %d chunks (doc_id=%s)", len(points), doc_id)
    return len(points)


# ═══════════════════════════════════════════════════════════════════
# 按文档 ID 删除
# ═══════════════════════════════════════════════════════════════════


def delete_by_doc_id(doc_id: str) -> None:
    """删除指定文档的所有向量（文档更新/删除时调用）。"""
    ensure_collection()
    client = _get_client()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_id",
                        match=models.MatchValue(value=doc_id),
                    )
                ]
            )
        ),
    )
    logger.info("已删除文档向量: doc_id=%s", doc_id)


# ═══════════════════════════════════════════════════════════════════
# 语义检索
# ═══════════════════════════════════════════════════════════════════


async def retrieve(
    query: str,
    *,
    top_k: int = 5,
    score_threshold: float = 0.5,
    doc_ids: list[str] | None = None,
) -> list[RetrievalResult]:
    """语义检索最相似的文档片段。

    Args:
        query: 用户查询文本。
        top_k: 返回的最大结果数。
        score_threshold: 最低相似度阈值（0~1）。
        doc_ids: 可选的文档 ID 过滤列表。

    Returns:
        按相似度降序排列的检索结果。
    """
    ensure_collection()
    client = _get_client()

    query_vector = await embed_query(query)

    query_filter = None
    if doc_ids:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="doc_id",
                    match=models.MatchAny(any=doc_ids),
                )
            ]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        score_threshold=score_threshold,
    ).points

    return [
        RetrievalResult(
            content=hit.payload.get("content", "") if hit.payload else "",
            score=hit.score if hit.score is not None else 0.0,
            metadata={
                "doc_id": hit.payload.get("doc_id", "") if hit.payload else "",
                "section_path": hit.payload.get("section_path", "") if hit.payload else "",
                "headers": hit.payload.get("headers", []) if hit.payload else [],
                "chunk_index": hit.payload.get("chunk_index", 0) if hit.payload else 0,
            },
            chunk_id=str(hit.id),
        )
        for hit in results
    ]


# ═══════════════════════════════════════════════════════════════════
# 格式化为 Prompt 上下文
# ═══════════════════════════════════════════════════════════════════


async def retrieve_as_context(
    query: str,
    *,
    top_k: int = 5,
    score_threshold: float = 0.5,
    doc_ids: list[str] | None = None,
) -> str | None:
    """检索并格式化为可直接注入 Prompt 的上下文字符串。

    返回 None 表示没有检索到相关内容。供 case_gen / diagnosis 等引擎
    通过 ``rag_context`` 参数注入 7 层 Prompt 的 Layer 6。
    """
    results = await retrieve(
        query,
        top_k=top_k,
        score_threshold=score_threshold,
        doc_ids=doc_ids,
    )
    if not results:
        return None

    parts: list[str] = []
    for i, r in enumerate(results, 1):
        source = r.metadata.get("section_path") or r.metadata.get("doc_id", "未知来源")
        parts.append(f"### 参考片段 {i}（相似度 {r.score:.2f} | {source}）\n{r.content}")

    return "\n\n".join(parts)
