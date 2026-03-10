"""B-M11-09 — KnowledgeService 单元测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

# ── Helpers ──────────────────────────────────────────────────────────


def _make_doc(
    title: str = "测试知识文档.md",
    doc_type: str = "md",
    content: str = "这是知识库内容",
    version: int = 1,
):
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.title = title
    doc.file_name = title
    doc.doc_type = doc_type
    doc.file_size = 1024
    doc.content = content
    doc.tags = ["测试", "知识库"]
    doc.source = "manual"
    doc.version = version
    doc.status = "active"
    doc.vector_status = "completed"
    doc.hit_count = 0
    doc.chunk_count = 2
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
                title="测试知识文档.md",
                file_name="测试知识文档.md",
                doc_type="md",
                file_size=128,
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
        docs = [_make_doc("标准文档.md", doc_type="md")]

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = docs

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[mock_count_result, mock_list_result])

        svc = _make_service(session)
        items, total = await svc.list_documents(doc_type="md")

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


class TestKnowledgeIndexing:
    async def test_upload_document_indexes_chunks(self):
        """上传文档后应完成解析、分块和向量索引。"""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        doc_mock = _make_doc()
        doc_mock.vector_status = "processing"
        doc_mock.chunk_count = 0

        upload = MagicMock()
        upload.filename = "知识库文档.md"
        upload.read = AsyncMock(return_value=b"# Title\n\ncontent")

        svc = _make_service(session)

        with (
            patch("app.modules.knowledge.service.KnowledgeDocument", return_value=doc_mock),
            patch(
                "app.modules.knowledge.service.parse_document",
                return_value=("# Title\n\ncontent", {"sections": []}),
            ),
            patch("app.modules.knowledge.service.chunk_by_headers", return_value=[MagicMock(), MagicMock()]),
            patch("app.modules.knowledge.service.index_chunks", new=AsyncMock(return_value=2)) as index_chunks,
        ):
            result = await svc.upload_document(upload)

        session.add.assert_called_once_with(doc_mock)
        session.commit.assert_awaited()
        index_chunks.assert_awaited_once()
        assert result == doc_mock
        assert doc_mock.vector_status == "completed"
        assert doc_mock.chunk_count == 2
