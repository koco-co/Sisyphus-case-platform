"""B-M13-07 — ExecutionService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.execution.schemas import ExecutionResultCreate


# ── Helpers ──────────────────────────────────────────────────────────


def _make_result(
    status: str = "passed",
    test_case_id: uuid.UUID | None = None,
    iteration_id: uuid.UUID | None = None,
):
    result = MagicMock()
    result.id = uuid.uuid4()
    result.test_case_id = test_case_id or uuid.uuid4()
    result.iteration_id = iteration_id or uuid.uuid4()
    result.executor_id = uuid.uuid4()
    result.status = status
    result.actual_result = "测试通过"
    result.defect_id = None
    result.environment = "staging"
    result.duration_seconds = 30
    result.executed_at = "2024-01-01T10:00:00"
    result.evidence = None
    result.deleted_at = None
    return result


def _make_service(session: AsyncMock):
    from app.modules.execution.service import ExecutionService

    return ExecutionService(session)


# ── Tests ────────────────────────────────────────────────────────────


class TestUpsertResult:
    async def test_upsert_new_result(self):
        """新结果应 insert 并返回。"""
        tc_id = uuid.uuid4()
        iter_id = uuid.uuid4()
        result_mock = _make_result(test_case_id=tc_id, iteration_id=iter_id)

        session = AsyncMock()
        svc = _make_service(session)

        # Mock record_result 完整逻辑: patch select 避免 SQLAlchemy 解析 mock model
        with patch("app.modules.execution.service.select") as mock_select:
            mock_select.return_value.where.return_value = MagicMock()

            mock_query_result = MagicMock()
            mock_query_result.scalar_one_or_none.return_value = None
            session.execute = AsyncMock(return_value=mock_query_result)
            session.add = MagicMock()
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            with patch("app.modules.execution.service.ExecutionResult", return_value=result_mock):
                result = await svc.record_result(
                    ExecutionResultCreate(
                        test_case_id=tc_id,
                        iteration_id=iter_id,
                        status="passed",
                    )
                )

        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    async def test_upsert_existing_result(self):
        """已有记录应 update 而非 insert（幂等）。"""
        tc_id = uuid.uuid4()
        iter_id = uuid.uuid4()
        existing = _make_result(status="passed", test_case_id=tc_id, iteration_id=iter_id)

        session = AsyncMock()
        svc = _make_service(session)

        with patch("app.modules.execution.service.select") as mock_select:
            mock_select.return_value.where.return_value = MagicMock()

            mock_query_result = MagicMock()
            mock_query_result.scalar_one_or_none.return_value = existing
            session.execute = AsyncMock(return_value=mock_query_result)
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            result = await svc.record_result(
                ExecutionResultCreate(
                    test_case_id=tc_id,
                    iteration_id=iter_id,
                    status="failed",
                    actual_result="测试失败",
                )
            )

        assert existing.status == "failed"
        session.commit.assert_awaited_once()


class TestMarkFailed:
    async def test_mark_failed(self):
        """mark_failed 应通过 record_result 记录失败结果。"""
        tc_id = uuid.uuid4()
        iter_id = uuid.uuid4()
        result_mock = _make_result(status="failed", test_case_id=tc_id, iteration_id=iter_id)
        result_mock.defect_id = "BUG-001"

        session = AsyncMock()
        svc = _make_service(session)

        # mark_failed 内部调用 record_result，直接 mock record_result
        with patch.object(svc, "record_result", return_value=result_mock) as mock_record:
            result = await svc.mark_failed(
                test_case_id=tc_id,
                iteration_id=iter_id,
                defect_id="BUG-001",
                actual_result="NPE 异常",
            )

        mock_record.assert_awaited_once()
        call_args = mock_record.call_args[0][0]
        assert call_args.status == "failed"
        assert call_args.defect_id == "BUG-001"

    async def test_mark_failed_creates_new_record(self):
        """无现有记录时 mark_failed 应创建新的失败记录。"""
        tc_id = uuid.uuid4()
        iter_id = uuid.uuid4()
        result_mock = _make_result(status="failed", test_case_id=tc_id, iteration_id=iter_id)

        session = AsyncMock()
        svc = _make_service(session)

        with patch("app.modules.execution.service.select") as mock_select:
            mock_select.return_value.where.return_value = MagicMock()

            mock_query_result = MagicMock()
            mock_query_result.scalar_one_or_none.return_value = None
            session.execute = AsyncMock(return_value=mock_query_result)
            session.add = MagicMock()
            session.commit = AsyncMock()
            session.refresh = AsyncMock()

            with patch("app.modules.execution.service.ExecutionResult", return_value=result_mock):
                result = await svc.mark_failed(
                    test_case_id=tc_id,
                    iteration_id=iter_id,
                    defect_id="BUG-002",
                )

        session.add.assert_called_once()
