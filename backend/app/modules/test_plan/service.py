from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.test_plan.models import TestPlan


class TestPlanService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_plans(self, iteration_id: UUID | None = None) -> list[TestPlan]:
        q = select(TestPlan).where(TestPlan.deleted_at.is_(None))
        if iteration_id:
            q = q.where(TestPlan.iteration_id == iteration_id)
        q = q.order_by(TestPlan.created_at.desc())
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_plan(self, plan_id: UUID) -> TestPlan | None:
        q = select(TestPlan).where(TestPlan.id == plan_id, TestPlan.deleted_at.is_(None))
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def create_plan(self, **kwargs: object) -> TestPlan:
        plan = TestPlan(**kwargs)
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def update_status(self, plan_id: UUID, status: str) -> TestPlan | None:
        plan = await self.get_plan(plan_id)
        if not plan:
            return None
        plan.status = status
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def soft_delete(self, plan_id: UUID) -> bool:
        plan = await self.get_plan(plan_id)
        if not plan:
            return False
        plan.deleted_at = datetime.now(UTC)
        await self.session.commit()
        return True
