from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.templates.models import TestCaseTemplate


class TemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_templates(
        self,
        category: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestCaseTemplate], int]:
        q = select(TestCaseTemplate).where(TestCaseTemplate.deleted_at.is_(None))
        count_q = select(func.count()).select_from(TestCaseTemplate).where(TestCaseTemplate.deleted_at.is_(None))

        if category:
            q = q.where(TestCaseTemplate.category == category)
            count_q = count_q.where(TestCaseTemplate.category == category)

        total = (await self.session.execute(count_q)).scalar() or 0
        q = q.order_by(TestCaseTemplate.usage_count.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_template(self, template_id: UUID) -> TestCaseTemplate | None:
        q = select(TestCaseTemplate).where(
            TestCaseTemplate.id == template_id,
            TestCaseTemplate.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def create_template(self, **kwargs) -> TestCaseTemplate:
        tpl = TestCaseTemplate(**kwargs)
        self.session.add(tpl)
        await self.session.commit()
        await self.session.refresh(tpl)
        return tpl

    async def use_template(self, template_id: UUID) -> TestCaseTemplate | None:
        tpl = await self.get_template(template_id)
        if not tpl:
            return None
        tpl.usage_count += 1
        await self.session.commit()
        await self.session.refresh(tpl)
        return tpl

    async def soft_delete(self, template_id: UUID) -> bool:
        from datetime import UTC, datetime

        tpl = await self.get_template(template_id)
        if not tpl:
            return False
        tpl.deleted_at = datetime.now(UTC)
        await self.session.commit()
        return True
