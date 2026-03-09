"""B-M20-06 — AuditService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.audit.schemas import AuditLogCreate


# ── Helpers ──────────────────────────────────────────────────────────


def _make_log(
    action: str = "create",
    entity_type: str = "test_case",
):
    log = MagicMock()
    log.id = uuid.uuid4()
    log.user_id = uuid.uuid4()
    log.action = action
    log.entity_type = entity_type
    log.entity_id = uuid.uuid4()
    log.old_value = None
    log.new_value = {"title": "新用例"}
    log.ip_address = "127.0.0.1"
    log.user_agent = "TestAgent"
    log.created_at = "2024-01-01T10:00:00"
    return log


def _make_service(session: AsyncMock):
    from app.modules.audit.service import AuditService

    return AuditService(session)


# ── Tests ────────────────────────────────────────────────────────────


class TestCreateLog:
    async def test_create_log(self):
        """应成功创建审计日志。"""
        session = AsyncMock()
        log_mock = _make_log()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)

        with patch("app.modules.audit.service.AuditLog", return_value=log_mock):
            result = await svc.log_action(
                AuditLogCreate(
                    action="create",
                    entity_type="test_case",
                    entity_id=log_mock.entity_id,
                    new_value={"title": "新用例"},
                )
            )

        session.add.assert_called_once_with(log_mock)
        session.commit.assert_awaited_once()

    async def test_create_log_with_old_value(self):
        """带旧值的审计日志应正确记录变更。"""
        session = AsyncMock()
        log_mock = _make_log(action="update")
        log_mock.old_value = {"title": "旧标题"}
        log_mock.new_value = {"title": "新标题"}
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)

        with patch("app.modules.audit.service.AuditLog", return_value=log_mock):
            result = await svc.log_action(
                AuditLogCreate(
                    action="update",
                    entity_type="test_case",
                    old_value={"title": "旧标题"},
                    new_value={"title": "新标题"},
                )
            )

        session.add.assert_called_once()


class TestEntityHistory:
    async def test_entity_history(self):
        """查询实体历史应返回按时间排序的日志。"""
        entity_id = uuid.uuid4()
        logs = [
            _make_log("create", "test_case"),
            _make_log("update", "test_case"),
            _make_log("update", "test_case"),
        ]
        for log in logs:
            log.entity_id = entity_id

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = logs

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.get_entity_history("test_case", entity_id)

        assert len(result) == 3
        assert result[0].action == "create"

    async def test_entity_history_empty(self):
        """无历史记录应返回空列表。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        svc = _make_service(session)
        result = await svc.get_entity_history("test_case", uuid.uuid4())

        assert result == []
