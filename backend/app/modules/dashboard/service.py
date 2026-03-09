from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import Iteration, Product, Requirement
from app.modules.testcases.models import TestCase


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_stats(self) -> dict:
        product_count = await self._count(Product)
        iteration_count = await self._count(Iteration)
        requirement_count = await self._count(Requirement)
        testcase_count = await self._count(TestCase)

        return {
            "product_count": product_count,
            "iteration_count": iteration_count,
            "requirement_count": requirement_count,
            "testcase_count": testcase_count,
            "coverage_rate": 0,
            "weekly_cases": 0,
            "pending_diagnosis": 0,
        }

    async def get_recent_activities(self, limit: int = 10) -> list[dict]:
        """Get recent activities from various tables."""
        activities: list[dict] = []

        q = (
            select(Requirement)
            .where(Requirement.deleted_at.is_(None))
            .order_by(Requirement.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(q)
        for req in result.scalars().all():
            activities.append(
                {
                    "time": req.created_at.isoformat() if req.created_at else "",
                    "action": f"创建需求 {req.req_id}",
                    "resource": "requirement",
                    "resource_id": str(req.id),
                    "title": req.title,
                }
            )

        q = select(TestCase).where(TestCase.deleted_at.is_(None)).order_by(TestCase.created_at.desc()).limit(limit)
        result = await self.session.execute(q)
        for tc in result.scalars().all():
            activities.append(
                {
                    "time": tc.created_at.isoformat() if tc.created_at else "",
                    "action": f"生成用例 {tc.case_id}",
                    "resource": "testcase",
                    "resource_id": str(tc.id),
                    "title": tc.title,
                }
            )

        activities.sort(key=lambda x: x["time"], reverse=True)
        return activities[:limit]

    async def get_products_overview(self) -> list[dict]:
        """Get overview of all products with stats."""
        q = select(Product).where(Product.deleted_at.is_(None))
        result = await self.session.execute(q)
        products = result.scalars().all()

        overview = []
        for p in products:
            iter_q = select(func.count()).where(
                Iteration.product_id == p.id,
                Iteration.deleted_at.is_(None),
            )
            iter_count = (await self.session.execute(iter_q)).scalar() or 0

            req_q = (
                select(func.count())
                .select_from(Requirement)
                .join(Iteration, Requirement.iteration_id == Iteration.id)
                .where(
                    Iteration.product_id == p.id,
                    Requirement.deleted_at.is_(None),
                )
            )
            req_count = (await self.session.execute(req_q)).scalar() or 0

            tc_q = (
                select(func.count())
                .select_from(TestCase)
                .join(Requirement, TestCase.requirement_id == Requirement.id)
                .join(Iteration, Requirement.iteration_id == Iteration.id)
                .where(
                    Iteration.product_id == p.id,
                    TestCase.deleted_at.is_(None),
                )
            )
            tc_count = (await self.session.execute(tc_q)).scalar() or 0

            overview.append(
                {
                    "id": str(p.id),
                    "name": p.name,
                    "slug": p.slug,
                    "description": p.description,
                    "iteration_count": iter_count,
                    "requirement_count": req_count,
                    "testcase_count": tc_count,
                    "status": "active",
                }
            )

        return overview

    async def _count(self, model) -> int:  # type: ignore[type-arg]
        q = select(func.count()).where(model.deleted_at.is_(None))
        result = await self.session.execute(q)
        return result.scalar() or 0
