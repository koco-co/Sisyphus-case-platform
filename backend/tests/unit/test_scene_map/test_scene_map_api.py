"""B-M04-11 — 场景地图 API 测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


class TestGenerateEndpoint:
    """测试场景地图生成端点。"""

    async def test_generate_endpoint(self):
        """POST /api/scene-map/{req_id}/generate 应返回 SSE 流。"""
        req_id = uuid.uuid4()

        mock_map = MagicMock()
        mock_map.id = uuid.uuid4()
        mock_map.requirement_id = req_id
        mock_map.status = "draft"

        mock_service_instance = AsyncMock()
        mock_service_instance.get_or_create = AsyncMock(return_value=mock_map)

        async def fake_stream():
            yield 'event: content\ndata: {"delta": "生成中..."}\n\n'

        mock_service_instance.generate_stream = AsyncMock(return_value=fake_stream())

        with patch("app.modules.scene_map.router.SceneMapService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(f"/api/scene-map/{req_id}/generate")

            app.dependency_overrides.clear()

        assert resp.status_code == 200


class TestConfirmEndpoint:
    """测试场景地图确认端点。"""

    async def test_confirm_endpoint(self):
        """POST /api/scene-map/{req_id}/confirm 应确认场景地图。"""
        req_id = uuid.uuid4()
        map_id = uuid.uuid4()

        # Build a properly structured mock that passes Pydantic validation
        mock_map = MagicMock()
        mock_map.id = map_id
        mock_map.requirement_id = req_id
        mock_map.status = "confirmed"
        mock_map.confirmed_at = None
        mock_map.created_at = "2024-01-01T00:00:00"
        mock_map.updated_at = "2024-01-01T00:00:00"
        mock_map.deleted_at = None

        mock_service_instance = AsyncMock()
        mock_service_instance.get_map = AsyncMock(return_value=mock_map)
        mock_service_instance.confirm_all = AsyncMock(return_value=mock_map)
        mock_service_instance.list_test_points = AsyncMock(return_value=[])

        # The endpoint uses response_model=SceneMapResponse, which calls model_validate.
        # We need to patch at the schema level to return valid data.
        from app.modules.scene_map.schemas import SceneMapResponse

        fake_resp = SceneMapResponse(
            id=map_id,
            requirement_id=req_id,
            status="confirmed",
            confirmed_at=None,
            test_points=[],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )

        with (
            patch("app.modules.scene_map.router.SceneMapService", return_value=mock_service_instance),
            patch("app.modules.scene_map.router.SceneMapResponse") as MockSceneMapResp,
        ):
            MockSceneMapResp.model_validate.return_value = fake_resp

            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(f"/api/scene-map/{req_id}/confirm")

            app.dependency_overrides.clear()

        assert resp.status_code == 200
