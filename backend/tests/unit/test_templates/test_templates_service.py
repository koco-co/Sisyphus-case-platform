"""B-M10-02 — Templates service tests."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock


def _make_template():
    return SimpleNamespace(
        id=uuid.uuid4(),
        name="API 接口测试模板",
        category="api",
        description="用于接口参数与权限校验",
        template_content={
            "precondition": "接口 {{endpoint}} 已完成鉴权配置",
            "steps": [
                {
                    "step": 1,
                    "action": "调用 {{endpoint}} 并携带 {{user}} 凭证",
                    "expected": "接口返回 200",
                },
                {
                    "step": 2,
                    "action": "移除必填参数再次调用 {{endpoint}}",
                    "expected": "返回 422 并提示参数错误",
                },
            ],
        },
        variables={"endpoint": "/api/search", "user": "tester"},
        usage_count=7,
        deleted_at=None,
    )


class TestApplyTemplate:
    async def test_apply_template_substitutes_variables_and_increments_usage(self):
        session = AsyncMock()
        service = _make_service(session)
        template = _make_template()

        service.get_template = AsyncMock(return_value=template)

        result = await service.apply_template(
            template.id,
            requirement_id=uuid.uuid4(),
            variables={"user": "admin"},
        )

        assert result["template_id"] == template.id
        assert result["applied_content"]["precondition"] == "接口 /api/search 已完成鉴权配置"
        assert result["applied_content"]["steps"][0]["action"] == "调用 /api/search 并携带 admin 凭证"
        assert template.usage_count == 8
        session.commit.assert_awaited_once()


class TestSoftDelete:
    async def test_soft_delete_marks_deleted_at(self):
        session = AsyncMock()
        service = _make_service(session)
        template = _make_template()

        service.get_template = AsyncMock(return_value=template)

        await service.soft_delete(template.id)

        assert template.deleted_at is not None
        session.commit.assert_awaited_once()


def _make_service(session: AsyncMock):
    from app.modules.templates.service import TemplateService

    return TemplateService(session)
