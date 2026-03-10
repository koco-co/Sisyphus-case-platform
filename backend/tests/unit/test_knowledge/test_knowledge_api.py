"""B-M11-10 — Knowledge API contract tests."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient


def _make_doc():
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.file_name = "知识库文档.md"
    doc.doc_type = "md"
    doc.file_size = 2048
    doc.vector_status = "completed"
    doc.hit_count = 3
    doc.chunk_count = 6
    doc.tags = ["知识库"]
    doc.created_at = "2024-01-01T00:00:00"
    doc.updated_at = "2024-01-01T00:00:00"
    doc.content = "# Title\n\ncontent"
    return doc


class TestKnowledgeListEndpoint:
    async def test_list_documents_matches_frontend_contract(self):
        """GET /api/knowledge/ 应返回知识库页面需要的字段。"""
        mock_doc = _make_doc()
        mock_service_instance = AsyncMock()
        mock_service_instance.list_documents = AsyncMock(return_value=([mock_doc], 1))

        with patch("app.modules.knowledge.router.KnowledgeService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/knowledge/?doc_type=md&vector_status=completed&q=知识")

            app.dependency_overrides.clear()

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] == 1
        assert payload["items"][0] == {
            "id": str(mock_doc.id),
            "file_name": "知识库文档.md",
            "doc_type": "md",
            "file_size": 2048,
            "vector_status": "completed",
            "hit_count": 3,
            "chunk_count": 6,
            "tags": ["知识库"],
            "uploaded_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }


class TestKnowledgeUploadEndpoint:
    async def test_upload_document_endpoint(self):
        """POST /api/knowledge/upload 应接收文件并返回已索引文档。"""
        mock_doc = _make_doc()
        mock_service_instance = AsyncMock()
        mock_service_instance.upload_document = AsyncMock(return_value=mock_doc)

        with patch("app.modules.knowledge.router.KnowledgeService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/knowledge/upload",
                    files={"file": ("knowledge.md", b"# hello\n\nworld", "text/markdown")},
                )

            app.dependency_overrides.clear()

        assert resp.status_code == 201
        assert resp.json()["file_name"] == "知识库文档.md"
        assert resp.json()["vector_status"] == "completed"


class TestKnowledgeReindexEndpoint:
    async def test_reindex_document_endpoint(self):
        """POST /api/knowledge/{id}/reindex 应返回重建后的文档信息。"""
        doc_id = uuid.uuid4()
        mock_doc = _make_doc()
        mock_service_instance = AsyncMock()
        mock_service_instance.reindex_document = AsyncMock(return_value=mock_doc)

        with patch("app.modules.knowledge.router.KnowledgeService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(f"/api/knowledge/{doc_id}/reindex")

            app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json()["chunk_count"] == 6


class TestKnowledgeSearchEndpoint:
    async def test_search_endpoint(self):
        """POST /api/knowledge/search 应返回 RAG 测试面板需要的结果格式。"""
        result = {
            "id": "chunk-1",
            "content": "导入失败时需要回滚并告警。",
            "score": 0.91,
            "source_doc": "知识库文档.md",
            "chunk_index": 0,
        }
        mock_service_instance = AsyncMock()
        mock_service_instance.search = AsyncMock(return_value=[result])

        with patch("app.modules.knowledge.router.KnowledgeService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post("/api/knowledge/search", json={"query": "导入失败如何处理", "top_k": 5})

            app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json() == [result]
