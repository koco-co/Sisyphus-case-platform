from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge.models import KnowledgeDocument


class KnowledgeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_documents(
        self,
        doc_type: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[KnowledgeDocument], int]:
        q = select(KnowledgeDocument).where(KnowledgeDocument.deleted_at.is_(None))
        count_q = select(func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.deleted_at.is_(None))

        if doc_type:
            q = q.where(KnowledgeDocument.doc_type == doc_type)
            count_q = count_q.where(KnowledgeDocument.doc_type == doc_type)
        if status:
            q = q.where(KnowledgeDocument.status == status)
            count_q = count_q.where(KnowledgeDocument.status == status)

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
        doc = KnowledgeDocument(**kwargs)
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

    async def soft_delete(self, doc_id: UUID) -> bool:
        from datetime import UTC, datetime

        doc = await self.get_document(doc_id)
        if not doc:
            return False
        doc.deleted_at = datetime.now(UTC)
        await self.session.commit()
        return True
