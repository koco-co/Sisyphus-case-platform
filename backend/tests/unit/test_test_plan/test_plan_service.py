"""B-M09-06 — TestPlanService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.test_plan.schemas import TestPlanCreate

# ── Helpers ──────────────────────────────────────────────────────────


def _make_plan(
    title: str = "Sprint-1 测试计划",
    status: str = "draft",
    planned_cases: int = 50,
    executed_cases: int = 0,
    passed_cases: int = 0,
    failed_cases: int = 0,
    blocked_cases: int = 0,
):
    plan = MagicMock()
    plan.id = uuid.uuid4()
    plan.iteration_id = uuid.uuid4()
    plan.title = title
    plan.description = "测试计划描述"
    plan.status = status
    plan.planned_cases = planned_cases
    plan.executed_cases = executed_cases
    plan.passed_cases = passed_cases
    plan.failed_cases = failed_cases
    plan.blocked_cases = blocked_cases
    plan.start_date = None
    plan.end_date = None
    plan.assigned_to = None
    plan.scope = None
    plan.deleted_at = None
    return plan


def _make_service(session: AsyncMock):
    from app.modules.test_plan.service import TestPlanService

    return TestPlanService(session)


# ── Tests ────────────────────────────────────────────────────────────


class TestCreatePlan:
    async def test_create_plan(self):
        """创建测试计划应持久化并返回对象。"""
        session = AsyncMock()
        plan_mock = _make_plan()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)

        with patch("app.modules.test_plan.service.TestPlan", return_value=plan_mock):
            result = await svc.create_plan(
                TestPlanCreate(
                    iteration_id=plan_mock.iteration_id,
                    title="Sprint-1 测试计划",
                    planned_cases=50,
                )
            )

        session.add.assert_called_once_with(plan_mock)
        session.commit.assert_awaited_once()
        assert result == plan_mock

    async def test_create_plan_with_scope(self):
        """创建带 scope 的测试计划。"""
        session = AsyncMock()
        plan_mock = _make_plan()
        plan_mock.scope = {"modules": ["login", "sync"]}
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)

        with patch("app.modules.test_plan.service.TestPlan", return_value=plan_mock):
            result = await svc.create_plan(
                TestPlanCreate(
                    iteration_id=plan_mock.iteration_id,
                    title="Scoped Plan",
                    scope={"modules": ["login", "sync"]},
                )
            )

        assert result.scope == {"modules": ["login", "sync"]}


class TestPlanStats:
    async def test_plan_stats(self):
        """统计应正确汇总各状态计划数和用例数。"""
        plans = [
            _make_plan("Plan A", "draft", 50, 0, 0, 0, 0),
            _make_plan("Plan B", "active", 100, 80, 60, 15, 5),
            _make_plan("Plan C", "completed", 30, 30, 28, 2, 0),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = plans

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.get_stats(plans[0].iteration_id)

        assert result.total_plans == 3
        assert result.draft == 1
        assert result.active == 1
        assert result.completed == 1
        assert result.total_planned == 180
        assert result.total_executed == 110
        assert result.total_passed == 88
        assert result.total_failed == 17
        assert result.total_blocked == 5
        assert result.pass_rate == pytest.approx(80.0, abs=0.1)

    async def test_plan_stats_empty(self):
        """无计划时统计应全为零。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.get_stats(uuid.uuid4())

        assert result.total_plans == 0
        assert result.pass_rate == 0.0
