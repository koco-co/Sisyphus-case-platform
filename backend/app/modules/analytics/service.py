from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import Iteration, Product, Requirement
from app.modules.testcases.models import TestCase


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_quality_overview(self) -> dict:
        product_count = (
            await self.session.execute(select(func.count()).select_from(Product).where(Product.deleted_at.is_(None)))
        ).scalar() or 0

        iteration_count = (
            await self.session.execute(
                select(func.count()).select_from(Iteration).where(Iteration.deleted_at.is_(None))
            )
        ).scalar() or 0

        requirement_count = (
            await self.session.execute(
                select(func.count()).select_from(Requirement).where(Requirement.deleted_at.is_(None))
            )
        ).scalar() or 0

        testcase_count = (
            await self.session.execute(select(func.count()).select_from(TestCase).where(TestCase.deleted_at.is_(None)))
        ).scalar() or 0

        return {
            "product_count": product_count,
            "iteration_count": iteration_count,
            "requirement_count": requirement_count,
            "testcase_count": testcase_count,
        }

    async def get_priority_distribution(self) -> list[dict]:
        q = select(TestCase.priority, func.count()).where(TestCase.deleted_at.is_(None)).group_by(TestCase.priority)
        result = await self.session.execute(q)
        return [{"priority": row[0], "count": row[1]} for row in result.all()]

    async def get_status_distribution(self) -> list[dict]:
        q = select(TestCase.status, func.count()).where(TestCase.deleted_at.is_(None)).group_by(TestCase.status)
        result = await self.session.execute(q)
        return [{"status": row[0], "count": row[1]} for row in result.all()]

    async def get_source_distribution(self) -> list[dict]:
        q = select(TestCase.source, func.count()).where(TestCase.deleted_at.is_(None)).group_by(TestCase.source)
        result = await self.session.execute(q)
        return [{"source": row[0], "count": row[1]} for row in result.all()]
