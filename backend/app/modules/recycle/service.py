from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import Product, Requirement
from app.modules.testcases.models import TestCase


class RecycleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_deleted_items(self, entity_type: str | None = None) -> list[dict]:
        items: list[dict] = []

        if entity_type is None or entity_type == "product":
            q = select(Product).where(Product.deleted_at.is_not(None))
            result = await self.session.execute(q)
            for p in result.scalars().all():
                items.append(
                    {
                        "id": str(p.id),
                        "entity_type": "product",
                        "name": p.name,
                        "deleted_at": p.deleted_at.isoformat() if p.deleted_at else "",
                    }
                )

        if entity_type is None or entity_type == "requirement":
            q = select(Requirement).where(Requirement.deleted_at.is_not(None))
            result = await self.session.execute(q)
            for r in result.scalars().all():
                items.append(
                    {
                        "id": str(r.id),
                        "entity_type": "requirement",
                        "name": r.title,
                        "deleted_at": r.deleted_at.isoformat() if r.deleted_at else "",
                    }
                )

        if entity_type is None or entity_type == "testcase":
            q = select(TestCase).where(TestCase.deleted_at.is_not(None))
            result = await self.session.execute(q)
            for tc in result.scalars().all():
                items.append(
                    {
                        "id": str(tc.id),
                        "entity_type": "testcase",
                        "name": tc.title,
                        "deleted_at": tc.deleted_at.isoformat() if tc.deleted_at else "",
                    }
                )

        items.sort(key=lambda x: x["deleted_at"], reverse=True)
        return items

    async def restore_item(self, entity_type: str, item_id: UUID) -> bool:
        model_map = {"product": Product, "requirement": Requirement, "testcase": TestCase}
        model = model_map.get(entity_type)
        if not model:
            return False

        item = await self.session.get(model, item_id)
        if not item or item.deleted_at is None:
            return False

        item.deleted_at = None
        await self.session.commit()
        return True

    async def permanent_delete(self, entity_type: str, item_id: UUID) -> bool:
        model_map = {"product": Product, "requirement": Requirement, "testcase": TestCase}
        model = model_map.get(entity_type)
        if not model:
            return False

        item = await self.session.get(model, item_id)
        if not item or item.deleted_at is None:
            return False

        await self.session.delete(item)
        await self.session.commit()
        return True
