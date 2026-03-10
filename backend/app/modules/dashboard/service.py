from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.schemas import DashboardActivityItem, DashboardPendingItem, DashboardStatsResponse
from app.modules.diagnosis.models import DiagnosisReport
from app.modules.products.models import Iteration, Product, Requirement
from app.modules.scene_map.models import SceneMap, TestPoint
from app.modules.testcases.models import TestCase


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_stats(self) -> DashboardStatsResponse:
        product_count = await self._count(Product)
        iteration_count = await self._count(Iteration)
        requirement_count = await self._count(Requirement)
        testcase_count = await self._count(TestCase)

        return DashboardStatsResponse(
            product_count=product_count,
            iteration_count=iteration_count,
            requirement_count=requirement_count,
            testcase_count=testcase_count,
            coverage_rate=0,
            weekly_cases=0,
            pending_diagnosis=0,
        )

    async def get_recent_activities(self, limit: int = 10) -> list[DashboardActivityItem]:
        """Get recent activities from various tables."""
        activities: list[DashboardActivityItem] = []

        q = (
            select(
                Requirement.id,
                Requirement.req_id,
                Requirement.title,
                Requirement.created_at,
            )
            .where(Requirement.deleted_at.is_(None))
            .order_by(Requirement.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(q)
        for req_id, req_code, title, created_at in result.all():
            activities.append(
                DashboardActivityItem(
                    id=f"requirement-{req_id}",
                    time=created_at or self._epoch(),
                    action=f"创建需求 {req_code}",
                    resource="requirement",
                    resource_id=str(req_id),
                    title=title,
                    user="系统",
                )
            )

        q = (
            select(
                TestCase.id,
                TestCase.case_id,
                TestCase.title,
                TestCase.created_at,
            )
            .where(TestCase.deleted_at.is_(None))
            .order_by(TestCase.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(q)
        for case_uuid, case_id, title, created_at in result.all():
            activities.append(
                DashboardActivityItem(
                    id=f"testcase-{case_uuid}",
                    time=created_at or self._epoch(),
                    action=f"生成用例 {case_id}",
                    resource="testcase",
                    resource_id=str(case_uuid),
                    title=title,
                    user="系统",
                )
            )

        activities.sort(key=lambda item: item.time, reverse=True)
        return activities[:limit]

    async def get_pending_items(self, limit: int = 10) -> list[DashboardPendingItem]:
        items: list[DashboardPendingItem] = []

        point_query = (
            select(
                TestPoint.id,
                TestPoint.title,
                TestPoint.priority,
                TestPoint.created_at,
                Product.name,
            )
            .select_from(TestPoint)
            .join(SceneMap, TestPoint.scene_map_id == SceneMap.id)
            .join(Requirement, SceneMap.requirement_id == Requirement.id)
            .join(Iteration, Requirement.iteration_id == Iteration.id)
            .join(Product, Iteration.product_id == Product.id)
            .where(
                TestPoint.deleted_at.is_(None),
                SceneMap.deleted_at.is_(None),
                Requirement.deleted_at.is_(None),
                Iteration.deleted_at.is_(None),
                Product.deleted_at.is_(None),
                TestPoint.status.in_(("pending", "ai_generated", "supplemented")),
            )
            .order_by(TestPoint.created_at.desc())
            .limit(limit)
        )
        point_rows = await self.session.execute(point_query)
        for point_id, title, priority, created_at, product_name in point_rows.all():
            items.append(
                DashboardPendingItem(
                    id=str(point_id),
                    type="unconfirmed_testpoint",
                    title=title,
                    description="场景地图中仍有待确认测试点",
                    product_name=product_name,
                    priority=self._map_priority(priority),
                    link="/scene-map",
                    created_at=created_at or self._epoch(),
                )
            )

        case_query = (
            select(
                TestCase.id,
                TestCase.title,
                TestCase.priority,
                TestCase.created_at,
                Product.name,
            )
            .select_from(TestCase)
            .join(Requirement, TestCase.requirement_id == Requirement.id)
            .join(Iteration, Requirement.iteration_id == Iteration.id)
            .join(Product, Iteration.product_id == Product.id)
            .where(
                TestCase.deleted_at.is_(None),
                Requirement.deleted_at.is_(None),
                Iteration.deleted_at.is_(None),
                Product.deleted_at.is_(None),
                TestCase.status.in_(("draft", "review", "rejected")),
            )
            .order_by(TestCase.created_at.desc())
            .limit(limit)
        )
        case_rows = await self.session.execute(case_query)
        for case_id, title, priority, created_at, product_name in case_rows.all():
            items.append(
                DashboardPendingItem(
                    id=str(case_id),
                    type="pending_review",
                    title=title,
                    description="AI 生成的用例已就绪，等待人工评审确认",
                    product_name=product_name,
                    priority=self._map_priority(priority),
                    link="/testcases",
                    created_at=created_at or self._epoch(),
                )
            )

        diagnosis_query = (
            select(
                DiagnosisReport.id,
                Requirement.title,
                DiagnosisReport.created_at,
                Product.name,
            )
            .select_from(DiagnosisReport)
            .join(Requirement, DiagnosisReport.requirement_id == Requirement.id)
            .join(Iteration, Requirement.iteration_id == Iteration.id)
            .join(Product, Iteration.product_id == Product.id)
            .where(
                DiagnosisReport.deleted_at.is_(None),
                Requirement.deleted_at.is_(None),
                Iteration.deleted_at.is_(None),
                Product.deleted_at.is_(None),
                DiagnosisReport.status == "failed",
            )
            .order_by(DiagnosisReport.created_at.desc())
            .limit(limit)
        )
        diagnosis_rows = await self.session.execute(diagnosis_query)
        for report_id, title, created_at, product_name in diagnosis_rows.all():
            items.append(
                DashboardPendingItem(
                    id=str(report_id),
                    type="failed_diagnosis",
                    title=title,
                    description="诊断流程执行失败，建议重新触发并检查输入",
                    product_name=product_name,
                    priority="high",
                    link="/diagnosis",
                    created_at=created_at or self._epoch(),
                )
            )

        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

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

    def _map_priority(self, priority: str | None) -> Literal["high", "medium", "low"]:
        if priority == "P0":
            return "high"
        if priority == "P1":
            return "medium"
        return "low"

    def _epoch(self) -> datetime:
        return datetime.fromtimestamp(0, tz=UTC)
