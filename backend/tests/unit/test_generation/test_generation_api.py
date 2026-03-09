"""B-M05-16 — 用例生成模块 API 测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


class TestGenerateEndpoint:
    """测试用例生成聊天端点。"""

    async def test_generate_endpoint(self):
        """POST /api/generation/sessions/{sid}/chat 应返回 SSE 流。"""
        session_id = uuid.uuid4()

        mock_gen_session = MagicMock()
        mock_gen_session.id = session_id
        mock_gen_session.requirement_id = uuid.uuid4()
        mock_gen_session.mode = "test_point_driven"
        mock_gen_session.status = "active"
        mock_gen_session.model_used = "gpt-4o"

        mock_service_instance = AsyncMock()
        mock_service_instance.get_session = AsyncMock(return_value=mock_gen_session)
        mock_service_instance.save_message = AsyncMock()

        async def fake_stream():
            yield 'event: content\ndata: {"delta": "用例生成中"}\n\n'

        mock_service_instance.chat_stream = AsyncMock(return_value=fake_stream())

        with patch("app.modules.generation.router.GenerationService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/generation/sessions/{session_id}/chat",
                    json={"message": "生成正常流程用例"},
                )

            app.dependency_overrides.clear()

        assert resp.status_code == 200


class TestFromTemplateEndpoint:
    """测试模板驱动生成端点。"""

    async def test_from_template_endpoint(self):
        """POST /api/generation/from-template 应请求成功或返回 404。"""
        mock_service_instance = AsyncMock()

        # from-template does raw SQL on session, so mock session.execute and session.get
        mock_session = AsyncMock()
        mock_tpl_result = MagicMock()
        mock_tpl_result.scalar_one_or_none.return_value = None  # template not found
        mock_session.execute = AsyncMock(return_value=mock_tpl_result)

        with patch("app.modules.generation.router.GenerationService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield mock_session

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/generation/from-template",
                    json={
                        "requirement_id": str(uuid.uuid4()),
                        "template_id": str(uuid.uuid4()),
                    },
                )

            app.dependency_overrides.clear()

        # Should be 404 since template doesn't exist
        assert resp.status_code == 404
