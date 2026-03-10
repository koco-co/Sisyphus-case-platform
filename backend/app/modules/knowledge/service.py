import logging
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.rag.chunker import chunk_by_headers, chunk_by_paragraphs
from app.engine.rag.retriever import delete_by_doc_id, index_chunks, retrieve
from app.modules.knowledge.models import KnowledgeDocument
from app.modules.uda.parsers import parse_document

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_documents(
        self,
        doc_type: str | None = None,
        vector_status: str | None = None,
        query: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[KnowledgeDocument], int]:
        q = select(KnowledgeDocument).where(KnowledgeDocument.deleted_at.is_(None))
        count_q = select(func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.deleted_at.is_(None))

        if doc_type:
            q = q.where(KnowledgeDocument.doc_type == doc_type)
            count_q = count_q.where(KnowledgeDocument.doc_type == doc_type)
        if vector_status:
            q = q.where(KnowledgeDocument.vector_status == vector_status)
            count_q = count_q.where(KnowledgeDocument.vector_status == vector_status)
        if query:
            like = f"%{query}%"
            search_clause = or_(
                KnowledgeDocument.file_name.ilike(like),
                KnowledgeDocument.title.ilike(like),
                KnowledgeDocument.content.ilike(like),
            )
            q = q.where(search_clause)
            count_q = count_q.where(search_clause)

        total = (await self.session.execute(count_q)).scalar() or 0
        q = q.order_by(KnowledgeDocument.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_document(self, doc_id: UUID) -> KnowledgeDocument | None:
        q = select(KnowledgeDocument).where(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def create_document(self, **kwargs) -> KnowledgeDocument:
        file_name = kwargs.get("file_name") or kwargs.get("title")
        if not file_name:
            raise ValueError("file_name is required")

        doc = KnowledgeDocument(
            title=kwargs.get("title") or Path(file_name).stem,
            file_name=file_name,
            doc_type=kwargs.get("doc_type", "md"),
            file_size=kwargs.get("file_size", 0),
            content=kwargs.get("content"),
            content_ast=kwargs.get("content_ast"),
            tags=kwargs.get("tags") or [],
            source=kwargs.get("source"),
            version=kwargs.get("version", 1),
            vector_status=kwargs.get("vector_status", "pending"),
            hit_count=kwargs.get("hit_count", 0),
            chunk_count=kwargs.get("chunk_count", 0),
            error_message=kwargs.get("error_message"),
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def update_document(self, doc_id: UUID, **kwargs) -> KnowledgeDocument | None:
        doc = await self.get_document(doc_id)
        if not doc:
            return None
        for key, value in kwargs.items():
            if hasattr(doc, key) and value is not None:
                setattr(doc, key, value)
        doc.version += 1
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def upload_document(self, file: UploadFile) -> KnowledgeDocument:
        raw_bytes = await file.read()
        filename = file.filename or "knowledge.txt"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
        if ext not in {"md", "docx", "pdf", "txt"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported knowledge file type: .{ext}",
            )

        doc = KnowledgeDocument(
            title=Path(filename).stem[:200],
            file_name=filename,
            doc_type=ext,
            file_size=len(raw_bytes),
            content=None,
            content_ast=None,
            tags=[],
            source="upload",
            version=1,
            vector_status="processing",
            hit_count=0,
            chunk_count=0,
            error_message=None,
        )
        self.session.add(doc)
        await self.session.flush()

        try:
            full_text, content_ast = parse_document(filename, raw_bytes)
            doc.content = full_text
            doc.content_ast = content_ast

            chunks = self._build_chunks(doc)
            if not chunks:
                raise ValueError("解析结果为空，无法建立向量索引")

            await index_chunks(chunks, doc_id=str(doc.id))
            doc.vector_status = "completed"
            doc.chunk_count = len(chunks)
            doc.error_message = None
            await self.session.commit()
            await self.session.refresh(doc)
            return doc
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to upload knowledge document: %s", filename)
            doc.vector_status = "failed"
            doc.error_message = str(exc)
            await self.session.commit()
            await self.session.refresh(doc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"知识库索引失败: {exc}",
            ) from exc

    async def reindex_document(self, doc_id: UUID) -> KnowledgeDocument:
        doc = await self.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        if not doc.content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document content is empty")

        try:
            doc.vector_status = "processing"
            doc.error_message = None
            delete_by_doc_id(str(doc.id))
            chunks = self._build_chunks(doc)
            if not chunks:
                raise ValueError("文档内容无法分块，无法重建索引")

            await index_chunks(chunks, doc_id=str(doc.id))
            doc.vector_status = "completed"
            doc.chunk_count = len(chunks)
            doc.version += 1
            await self.session.commit()
            await self.session.refresh(doc)
            return doc
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to reindex knowledge document: %s", doc_id)
            doc.vector_status = "failed"
            doc.error_message = str(exc)
            await self.session.commit()
            await self.session.refresh(doc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"重建索引失败: {exc}",
            ) from exc

    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        score_threshold: float = 0.5,
        doc_id: UUID | None = None,
    ) -> list[dict]:
        doc_ids = [str(doc_id)] if doc_id else None
        results = await retrieve(
            query,
            top_k=top_k,
            score_threshold=score_threshold,
            doc_ids=doc_ids,
        )
        if not results:
            return []

        result_doc_ids = [str(result.metadata.get("doc_id", "")) for result in results if result.metadata.get("doc_id")]
        doc_name_map = await self._get_doc_name_map(result_doc_ids)
        await self._increment_hit_counts(result_doc_ids)

        return [
            {
                "id": result.chunk_id,
                "content": result.content,
                "score": result.score,
                "source_doc": doc_name_map.get(
                    str(result.metadata.get("doc_id", "")),
                    str(result.metadata.get("doc_id", "")),
                ),
                "chunk_index": int(result.metadata.get("chunk_index", 0) or 0),
            }
            for result in results
        ]

    async def soft_delete(self, doc_id: UUID) -> bool:
        doc = await self.get_document(doc_id)
        if not doc:
            return False
        delete_by_doc_id(str(doc.id))
        doc.deleted_at = datetime.now(UTC)
        await self.session.commit()
        return True

    def _build_chunks(self, doc: KnowledgeDocument) -> list:
        content = (doc.content or "").strip()
        if not content:
            return []

        source_id = str(doc.id)
        if doc.doc_type == "md":
            chunks = chunk_by_headers(content, source_id=source_id)
            if chunks:
                return chunks
        return chunk_by_paragraphs(content, source_id=source_id)

    async def _get_doc_name_map(self, doc_ids: list[str]) -> dict[str, str]:
        normalized_ids = []
        for doc_id in doc_ids:
            try:
                normalized_ids.append(UUID(doc_id))
            except (TypeError, ValueError):
                continue

        if not normalized_ids:
            return {}

        result = await self.session.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id.in_(normalized_ids),
                KnowledgeDocument.deleted_at.is_(None),
            )
        )
        docs = list(result.scalars().all())
        return {str(doc.id): doc.file_name for doc in docs}

    async def _increment_hit_counts(self, doc_ids: list[str]) -> None:
        if not doc_ids:
            return

        hit_counts = Counter(doc_ids)
        result = await self.session.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id.in_([UUID(doc_id) for doc_id in hit_counts]),
                KnowledgeDocument.deleted_at.is_(None),
            )
        )
        docs = list(result.scalars().all())
        if not docs:
            return

        for doc in docs:
            doc.hit_count += hit_counts.get(str(doc.id), 0)

        await self.session.commit()
