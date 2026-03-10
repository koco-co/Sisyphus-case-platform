"""B-M10-01 — Templates API contract tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient


def _make_template():
    return SimpleNamespace(
        id=uuid.uuid4(),
        name="登录功能标准模板",
        category="functional",
        description="覆盖登录主流程与异常场景",
        template_content={
            "precondition": "已准备{{username}}账号",
            "steps": [
                {
                    "step": 1,
                    "action": "输入{{username}}和正确密码",
                    "expected": "登录成功",
                }
            ],
        },
        variables={"username": "tester"},
        usage_count=3,
        is_builtin=True,
        created_by=None,
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
    )


class TestTemplateListEndpoint:
    async def test_list_endpoint_matches_frontend_contract(self):
        template = _make_template()
        mock_service_instance = AsyncMock()
        mock_service_instance.list_templates = AsyncMock(return_value=([template], 1))

        with patch("app.modules.templates.router.TemplateService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/templates")

            app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["page"] == 1
        assert body["page_size"] == 20
        assert body["items"][0]["name"] == "登录功能标准模板"
        assert body["items"][0]["usage_count"] == 3
        assert body["items"][0]["is_builtin"] is True


class TestTemplateCreateEndpoint:
    async def test_create_endpoint_returns_created_template(self):
        template = _make_template()
        mock_service_instance = AsyncMock()
        mock_service_instance.create_template = AsyncMock(return_value=template)

        with patch("app.modules.templates.router.TemplateService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/templates",
                    json={
                        "name": "登录功能标准模板",
                        "category": "functional",
                        "description": "覆盖登录主流程与异常场景",
                        "template_content": {
                            "precondition": "已准备{{username}}账号",
                            "steps": [
                                {
                                    "step": 1,
                                    "action": "输入{{username}}和正确密码",
                                    "expected": "登录成功",
                                }
                            ],
                        },
                        "variables": {"username": "tester"},
                    },
                )

            app.dependency_overrides.clear()

        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "登录功能标准模板"
        assert body["template_content"]["steps"][0]["action"] == "输入{{username}}和正确密码"
        assert body["variables"] == {"username": "tester"}
