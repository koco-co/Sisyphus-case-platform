"""B-M14-06 — AnalyticsService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Helpers ──────────────────────────────────────────────────────────


def _make_service(session: AsyncMock):
    from app.modules.analytics.service import AnalyticsService

    return AnalyticsService(session)


# ── Tests ────────────────────────────────────────────────────────────


class TestDashboardSummary:
    async def test_dashboard_summary(self):
        """仪表盘汇总应返回包含各类分布数据的字典。"""
        iteration_id = uuid.uuid4()

        session = AsyncMock()
        svc = _make_service(session)

        with (
            patch.object(svc, "_count_cases_for_iteration", return_value=100),
            patch.object(
                svc,
                "_get_execution_counts",
                return_value={"passed": 60, "failed": 15, "blocked": 5, "skipped": 0},
            ),
            patch.object(
                svc,
                "get_priority_distribution",
                return_value=[{"priority": "P0", "count": 10}, {"priority": "P1", "count": 50}],
            ),
            patch.object(
                svc,
                "get_status_distribution",
                return_value=[{"status": "draft", "count": 20}, {"status": "approved", "count": 70}],
            ),
            patch.object(
                svc,
                "get_source_distribution",
                return_value=[{"source": "ai_generated", "count": 60}],
            ),
        ):
            result = await svc.get_dashboard_data(iteration_id)

        assert "overview" in result
        assert "priority_distribution" in result
        assert "status_distribution" in result
        assert "source_distribution" in result
        assert result["overview"]["total_cases"] == 100

    async def test_dashboard_empty_iteration(self):
        """空迭代的仪表盘应返回零值。"""
        session = AsyncMock()
        svc = _make_service(session)

        with (
            patch.object(svc, "_count_cases_for_iteration", return_value=0),
            patch.object(svc, "_get_execution_counts", return_value={}),
            patch.object(svc, "get_priority_distribution", return_value=[]),
            patch.object(svc, "get_status_distribution", return_value=[]),
            patch.object(svc, "get_source_distribution", return_value=[]),
        ):
            result = await svc.get_dashboard_data(uuid.uuid4())

        assert result["overview"]["total_cases"] == 0


class TestTrendData:
    async def test_trend_data(self):
        """趋势数据应包含日期和指标。"""
        from datetime import date

        iteration_id = uuid.uuid4()

        snap1 = MagicMock()
        snap1.snapshot_date = date(2024, 1, 1)
        snap1.metrics = {"total_cases": 50, "passed": 40, "failed": 5, "blocked": 2, "coverage_rate": 0.8, "defect_density": 0.1}

        snap2 = MagicMock()
        snap2.snapshot_date = date(2024, 1, 2)
        snap2.metrics = {"total_cases": 60, "passed": 50, "failed": 3, "blocked": 1, "coverage_rate": 0.85, "defect_density": 0.05}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snap1, snap2]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.get_trend_data(iteration_id)

        assert "dates" in result
        assert "metrics" in result
        assert len(result["dates"]) == 2
        assert "total_cases" in result["metrics"]

    async def test_trend_data_empty(self):
        """无快照时趋势数据应为空。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.get_trend_data(uuid.uuid4())

        assert result["dates"] == []
