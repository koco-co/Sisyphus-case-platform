"""B-M05-17 — 用例生成服务测试。"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.dialects import postgresql


def _compile_sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


class TestGetOrCreateSession:
    async def test_get_or_create_session_filters_by_mode(self):
        """复用会话查询应限制在相同生成模式内。"""
        from app.modules.generation.service import GenerationService

        requirement_id = uuid.uuid4()
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        service = GenerationService(session)

        with patch.object(service, "create_session", AsyncMock()) as create_session:
            await service.get_or_create_session(requirement_id, mode="dialogue")

        sql = _compile_sql(session.execute.await_args.args[0])
        assert "generation_sessions.mode = 'dialogue'" in sql
        create_session.assert_awaited_once_with(requirement_id, "dialogue")
