"""API 路由冒烟测试 — 验证所有已注册模块的基础端点返回 2xx。

NOTE: 需要完整的应用上下文（依赖 Docker 环境中的 PG/Redis）。
      如果无数据库连接，测试会被标记为 skip。
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.database import get_async_session_context
from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def smoke_client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_health(smoke_client: AsyncClient):
    resp = await smoke_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


_LIST_ENDPOINTS = [
    "/api/products",
    "/api/analytics/overview",
    "/api/search?q=test&types=requirement",
    "/api/dashboard/activities?limit=10",
    "/api/dashboard/pending-items",
    "/api/testcases",
]


@pytest.mark.parametrize("path", _LIST_ENDPOINTS)
async def test_list_endpoints_return_2xx(smoke_client: AsyncClient, path: str):
    """各模块的列表端点应当返回 2xx（即使数据为空）。"""
    resp = await smoke_client.get(path)
    assert 200 <= resp.status_code < 300, f"{path} returned {resp.status_code}: {resp.text[:200]}"


async def test_scene_map_endpoint_returns_2xx_for_existing_map(smoke_client: AsyncClient):
    """已有场景地图的需求，其场景地图接口应可正常读取。"""
    async with get_async_session_context() as session:
        result = await session.execute(
            text("SELECT requirement_id FROM scene_maps WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 1")
        )
        requirement_id = result.scalar_one_or_none()

    if requirement_id is None:
        pytest.skip("No scene map data available")

    resp = await smoke_client.get(f"/api/scene-map/{requirement_id}")
    assert 200 <= resp.status_code < 300, (
        f"/api/scene-map/{requirement_id} returned {resp.status_code}: {resp.text[:200]}"
    )
