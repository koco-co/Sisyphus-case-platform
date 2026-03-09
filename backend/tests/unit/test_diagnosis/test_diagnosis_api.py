"""B-M03-15 — 诊断模块 API 测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


# ── Tests ────────────────────────────────────────────────────────────


class TestScanEndpoint:
    """测试诊断扫描端点。"""

    async def test_scan_endpoint_creates_report(self):
        """POST /api/diagnosis/{req_id}/run 应触发扫描流程并返回 SSE 流。"""
        req_id = uuid.uuid4()

        mock_report = MagicMock()
        mock_report.id = uuid.uuid4()
        mock_report.requirement_id = req_id
        mock_report.status = "scanning"

        mock_service_instance = AsyncMock()
        mock_service_instance.create_or_get_report = AsyncMock(return_value=mock_report)

        async def fake_stream():
            yield 'event: content\ndata: {"delta": "分析中..."}\n\n'

        mock_service_instance.run_stream = AsyncMock(return_value=fake_stream())

        with patch("app.modules.diagnosis.router.DiagnosisService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(f"/api/diagnosis/{req_id}/run")

            app.dependency_overrides.clear()

        assert resp.status_code == 200


class TestChatEndpoint:
    """测试诊断对话端点。"""

    async def test_chat_endpoint(self):
        """POST /api/diagnosis/{req_id}/chat 应接受消息并返回流式响应。"""
        req_id = uuid.uuid4()

        mock_report = MagicMock()
        mock_report.id = uuid.uuid4()
        mock_report.requirement_id = req_id
        mock_report.status = "completed"

        mock_service_instance = AsyncMock()
        mock_service_instance.create_or_get_report = AsyncMock(return_value=mock_report)
        mock_service_instance.save_message = AsyncMock()

        async def fake_stream():
            yield 'event: content\ndata: {"delta": "回答"}\n\n'

        mock_service_instance.chat_stream = AsyncMock(return_value=fake_stream())

        with patch("app.modules.diagnosis.router.DiagnosisService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/diagnosis/{req_id}/chat",
                    json={"message": "数据同步的异常处理策略是什么？"},
                )

            app.dependency_overrides.clear()

        assert resp.status_code == 200
