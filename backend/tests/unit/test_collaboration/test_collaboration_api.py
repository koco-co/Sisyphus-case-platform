"""Collaboration API contract tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient


def _make_review():
    reviewer_id = uuid.uuid4()
    return SimpleNamespace(
        id=uuid.uuid4(),
        entity_type="requirement",
        entity_id=uuid.uuid4(),
        title="登录测试点评审",
        description="请确认认证主流程覆盖。",
        created_by=uuid.uuid4(),
        status="pending",
        reviewer_ids=[reviewer_id],
        decisions=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )


class TestSharedReviewEndpoint:
    async def test_shared_review_returns_entity_snapshot(self):
        """GET /api/collaboration/shared/{token} 应包含共享页所需的实体快照。"""
        review = _make_review()
        mock_service_instance = AsyncMock()
        mock_service_instance.get_review_by_token = AsyncMock(
            return_value={
                "review": review,
                "decisions": [],
                "entity_snapshot": {
                    "requirement_title": "用户登录功能需求",
                    "req_id": "REQ-LOGIN-001",
                    "test_points": [
                        {
                            "id": str(uuid.uuid4()),
                            "group_name": "认证",
                            "title": "正常登录",
                            "description": "验证合法账号密码登录成功",
                            "priority": "P1",
                            "status": "pending",
                            "source": "document",
                            "estimated_cases": 2,
                        }
                    ],
                    "reviewer_names": ["张三"],
                },
            }
        )

        with patch("app.modules.collaboration.router.CollaborationService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/collaboration/shared/share-token")

            app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert body["review"]["title"] == "登录测试点评审"
        assert body["entity_snapshot"]["requirement_title"] == "用户登录功能需求"
        assert body["entity_snapshot"]["test_points"][0]["title"] == "正常登录"
        assert body["entity_snapshot"]["reviewer_names"] == ["张三"]
