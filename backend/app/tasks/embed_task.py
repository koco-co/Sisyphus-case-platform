"""向量化嵌入异步任务 — 对知识库文档执行 embedding 后写入向量库。"""

from __future__ import annotations

import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.embed_task.embed_document", max_retries=3)
def embed_document(self, document_id: str, content: str, metadata: dict | None = None) -> dict:
    """对文档内容执行向量嵌入并写入 Qdrant。

    Args:
        document_id: 文档 ID
        content: 文档文本内容
        metadata: 附加元数据
    """
    self.update_state(state="STARTED", meta={"step": "embedding", "progress": 0})

    try:
        # 分段
        chunks = _split_text(content)
        self.update_state(state="STARTED", meta={"step": "chunking", "progress": 20, "chunks": len(chunks)})

        # TODO: 调用 embedding 模型生成向量，写入 Qdrant
        # 当前为占位实现，后续接入 engine/rag 模块
        logger.info("向量嵌入任务完成: document_id=%s, chunks=%d", document_id, len(chunks))

        self.update_state(state="STARTED", meta={"step": "complete", "progress": 100})
        return {"status": "success", "document_id": document_id, "chunks": len(chunks)}

    except Exception as exc:
        logger.error("向量嵌入任务失败 document_id=%s: %s", document_id, exc, exc_info=True)
        try:
            self.retry(exc=exc, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            return {"status": "failed", "error": str(exc)}
    return {"status": "failed", "error": "unknown"}


def _split_text(text: str, *, max_chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """简单按字符分段。"""
    if len(text) <= max_chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + max_chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
