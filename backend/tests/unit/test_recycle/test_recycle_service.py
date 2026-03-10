"""RecycleService 回归测试。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from app.modules.recycle.service import RecycleService


def _make_template(name: str = "接口模板") -> MagicMock:
    template = MagicMock()
    template.id = uuid.uuid4()
    template.name = name
    template.deleted_at = datetime.now(UTC)
    return template


def _make_knowledge(title: str = "知识文档") -> MagicMock:
    document = MagicMock()
    document.id = uuid.uuid4()
    document.title = title
    document.deleted_at = datetime.now(UTC)
    return document


class TestExtendedRecycleEntities:
    async def test_list_deleted_returns_template_items(self):
        """回收站列表应支持模板实体。"""
        template = _make_template()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [template]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        service = RecycleService(session)
        items, total = await service.list_deleted("template")

        assert total == 1
        assert items[0].entity_type == "template"
        assert items[0].name == "接口模板"

    async def test_list_deleted_returns_knowledge_items(self):
        """回收站列表应支持知识文档实体。"""
        document = _make_knowledge()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [document]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        service = RecycleService(session)
        items, total = await service.list_deleted("knowledge")

        assert total == 1
        assert items[0].entity_type == "knowledge"
        assert items[0].name == "知识文档"

    async def test_restore_supports_template_entities(self):
        """恢复动作应支持模板实体。"""
        template = _make_template()
        session = AsyncMock()
        session.get = AsyncMock(return_value=template)

        service = RecycleService(session)
        await service.restore("template", template.id)

        assert template.deleted_at is None
        session.commit.assert_awaited_once()
