"""B-M11-09 — KnowledgeService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


# ── Helpers ──────────────────────────────────────────────────────────


def _make_doc(
    title: str = "测试知识文档",
    doc_type: str = "standard",
    content: str = "这是知识库内容",
    version: int = 1,
):
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.title = title
    doc.doc_type = doc_type
    doc.content = content
    doc.tags = ["测试", "知识库"]
    doc.source = "manual"
    doc.version = version
    doc.status = "active"
    doc.deleted_at = None
    doc.created_at = "2024-01-01T00:00:00"
    doc.updated_at = "2024-01-01T00:00:00"
    return doc


def _make_service(session: AsyncMock):
    from app.modules.knowledge.service import KnowledgeService

    return KnowledgeService(session)


# ── Tests ────────────────────────────────────────────────────────────


class TestCreateDocument:
    async def test_create_document(self):
        """创建知识文档应持久化并返回对象。"""
        session = AsyncMock()
        doc_mock = _make_doc()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        svc = _make_service(session)

        with patch("app.modules.knowledge.service.KnowledgeDocument", return_value=doc_mock):
            result = await svc.create_document(
                title="测试知识文档",
                doc_type="standard",
                content="内容",
            )

        session.add.assert_called_once_with(doc_mock)
        session.commit.assert_awaited_once()
        assert result == doc_mock


class TestSearchKnowledge:
    async def test_list_documents(self):
        """列表查询应返回符合条件的文档和总数。"""
        docs = [_make_doc("文档A"), _make_doc("文档B")]

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = docs

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[mock_count_result, mock_list_result])

        svc = _make_service(session)
        items, total = await svc.list_documents()

        assert len(items) == 2
        assert total == 2
        assert items[0].title == "文档A"

    async def test_list_by_doc_type(self):
        """按类型过滤应正常工作。"""
        docs = [_make_doc("标准文档", doc_type="standard")]

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = docs

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[mock_count_result, mock_list_result])

        svc = _make_service(session)
        items, total = await svc.list_documents(doc_type="standard")

        assert len(items) == 1
        assert total == 1

    async def test_list_empty(self):
        """无匹配时返回空列表。"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[mock_count_result, mock_list_result])

        svc = _make_service(session)
        items, total = await svc.list_documents()

        assert items == []
        assert total == 0
