from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge.models import KnowledgeDocument
from app.modules.products.models import Iteration, Product, Requirement
from app.modules.recycle.schemas import RecycleItemResponse, RestoreRequest
from app.modules.templates.models import TestCaseTemplate
from app.modules.testcases.models import TestCase

_MODEL_MAP: dict[str, tuple[type, str]] = {
    "product": (Product, "name"),
    "iteration": (Iteration, "name"),
    "requirement": (Requirement, "title"),
    "testcase": (TestCase, "title"),
    "template": (TestCaseTemplate, "name"),
    "knowledge": (KnowledgeDocument, "title"),
}


class RecycleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_deleted(
        self,
        entity_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[RecycleItemResponse], int]:
        items: list[RecycleItemResponse] = []

        targets = {entity_type: _MODEL_MAP[entity_type]} if entity_type and entity_type in _MODEL_MAP else _MODEL_MAP

        for et, (model, name_field) in targets.items():
            q = select(model).where(model.deleted_at.is_not(None))
            result = await self.session.execute(q)
            for row in result.scalars().all():
                items.append(
                    RecycleItemResponse(
                        id=row.id,
                        entity_type=et,
                        name=getattr(row, name_field, ""),
                        deleted_at=row.deleted_at.isoformat() if row.deleted_at else "",
                    )
                )

        items.sort(key=lambda x: x.deleted_at, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return items[start : start + page_size], total

    async def restore(self, entity_type: str, entity_id: UUID) -> None:
        entry = _MODEL_MAP.get(entity_type)
        if not entry:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown entity type: {entity_type}")
        model = entry[0]

        item = await self.session.get(model, entity_id)
        if not item or item.deleted_at is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or not deleted")

        item.deleted_at = None
        await self.session.commit()

    async def permanent_delete(self, entity_type: str, entity_id: UUID) -> None:
        entry = _MODEL_MAP.get(entity_type)
        if not entry:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown entity type: {entity_type}")
        model = entry[0]

        item = await self.session.get(model, entity_id)
        if not item or item.deleted_at is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or not deleted")

        await self.session.delete(item)
        await self.session.commit()

    async def batch_restore(self, items: list[RestoreRequest]) -> int:
        restored = 0
        for req in items:
            entry = _MODEL_MAP.get(req.entity_type)
            if not entry:
                continue
            model = entry[0]
            item = await self.session.get(model, req.entity_id)
            if item and item.deleted_at is not None:
                item.deleted_at = None
                restored += 1
        await self.session.commit()
        return restored

    async def cleanup_expired(self, retention_days: int = 30) -> int:
        """Permanently delete soft-deleted records older than retention_days."""
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        deleted_count = 0

        for _et, (model, _name_field) in _MODEL_MAP.items():
            q = select(model).where(
                model.deleted_at.is_not(None),
                model.deleted_at < cutoff,
            )
            result = await self.session.execute(q)
            rows = result.scalars().all()
            for row in rows:
                await self.session.delete(row)
                deleted_count += 1

        await self.session.commit()
        return deleted_count
