from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.test_plan.models import TestPlan
from app.modules.test_plan.schemas import TestPlanCreate, TestPlanStatsResponse, TestPlanUpdate


class TestPlanService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_plans(
        self,
        iteration_id: UUID | None = None,
        status_filter: str | None = None,
    ) -> list[TestPlan]:
        q = select(TestPlan).where(TestPlan.deleted_at.is_(None))
        if iteration_id:
            q = q.where(TestPlan.iteration_id == iteration_id)
        if status_filter:
            q = q.where(TestPlan.status == status_filter)
        q = q.order_by(TestPlan.created_at.desc())
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_plan(self, plan_id: UUID) -> TestPlan:
        plan = await self.session.get(TestPlan, plan_id)
        if not plan or plan.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test plan not found",
            )
        return plan

    async def create_plan(self, data: TestPlanCreate) -> TestPlan:
        plan = TestPlan(**data.model_dump())
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def update_plan(self, plan_id: UUID, data: TestPlanUpdate) -> TestPlan:
        plan = await self.get_plan(plan_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(plan, key, value)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def soft_delete(self, plan_id: UUID) -> None:
        plan = await self.get_plan(plan_id)
        plan.deleted_at = datetime.now(UTC)
        await self.session.commit()

    async def get_stats(self, iteration_id: UUID) -> TestPlanStatsResponse:
        plans = await self.list_plans(iteration_id=iteration_id)
        draft = sum(1 for p in plans if p.status == "draft")
        active = sum(1 for p in plans if p.status == "active")
        completed = sum(1 for p in plans if p.status == "completed")
        total_planned = sum(p.planned_cases for p in plans)
        total_executed = sum(p.executed_cases for p in plans)
        total_passed = sum(p.passed_cases for p in plans)
        total_failed = sum(p.failed_cases for p in plans)
        total_blocked = sum(p.blocked_cases for p in plans)
        pass_rate = round(total_passed / total_executed * 100, 1) if total_executed else 0.0

        return TestPlanStatsResponse(
            total_plans=len(plans),
            draft=draft,
            active=active,
            completed=completed,
            total_planned=total_planned,
            total_executed=total_executed,
            total_passed=total_passed,
            total_failed=total_failed,
            total_blocked=total_blocked,
            pass_rate=pass_rate,
        )
