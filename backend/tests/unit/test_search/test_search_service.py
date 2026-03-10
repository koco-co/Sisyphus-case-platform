"""SearchService 回归测试。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from app.modules.search.service import SearchService


def _make_requirement(title: str = "Test Requirement") -> MagicMock:
    requirement = MagicMock()
    requirement.id = uuid.uuid4()
    requirement.title = title
    requirement.req_id = "REQ-001"
    requirement.updated_at = None
    return requirement


def _make_template(name: str = "API 模板") -> MagicMock:
    template = MagicMock()
    template.id = uuid.uuid4()
    template.name = name
    template.description = "接口测试模板说明"
    template.updated_at = datetime.now(UTC)
    return template


def _make_knowledge(title: str = "测试规范文档") -> MagicMock:
    document = MagicMock()
    document.id = uuid.uuid4()
    document.title = title
    document.doc_type = "md"
    document.source = "manual"
    document.updated_at = datetime.now(UTC)
    return document


def _make_diagnosis(summary: str = "登录流程存在验证码缺失风险") -> MagicMock:
    report = MagicMock()
    report.id = uuid.uuid4()
    report.summary = summary
    report.status = "completed"
    report.risk_count_high = 2
    report.risk_count_medium = 1
    report.updated_at = datetime.now(UTC)
    return report


class TestGlobalSearchFallback:
    async def test_global_search_rolls_back_before_ilike_fallback(self):
        """FTS 失败后应先回滚事务，再退回 ILIKE。"""
        requirement = _make_requirement()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [requirement]

        session = AsyncMock()

        async def execute(*_args, **_kwargs):
            if session.execute.await_count == 1:
                raise RuntimeError("fts failed")
            if session.rollback.await_count == 0:
                raise RuntimeError("rollback missing")
            return result

        session.execute.side_effect = execute
        session.rollback = AsyncMock()

        service = SearchService(session)
        items, total = await service.global_search("test", ["requirement"])

        session.rollback.assert_awaited_once()
        assert total == 1
        assert items[0].title == "Test Requirement"


class TestExtendedEntitySearch:
    async def test_global_search_returns_template_items(self):
        """模板应参与全局搜索并返回名称与描述摘要。"""
        template = _make_template()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [template]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        service = SearchService(session)
        items, total = await service.global_search("API", ["template"])

        assert total == 1
        assert items[0].entity_type == "template"
        assert items[0].title == "API 模板"
        assert items[0].summary == "接口测试模板说明"

    async def test_global_search_returns_knowledge_items(self):
        """知识文档应参与全局搜索并展示文档来源摘要。"""
        document = _make_knowledge()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [document]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        service = SearchService(session)
        items, total = await service.global_search("规范", ["knowledge"])

        assert total == 1
        assert items[0].entity_type == "knowledge"
        assert items[0].title == "测试规范文档"
        assert items[0].summary == "manual · md"

    async def test_global_search_returns_diagnosis_items(self):
        """诊断报告应参与全局搜索并展示风险统计。"""
        report = _make_diagnosis()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [report]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        service = SearchService(session)
        items, total = await service.global_search("验证码", ["diagnosis"])

        assert total == 1
        assert items[0].entity_type == "diagnosis"
        assert items[0].title == "登录流程存在验证码缺失风险"
        assert items[0].summary == "状态 completed · 高风险 2 · 中风险 1"
