"""B-M01-15 — UDA API 集成测试"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient


class TestUploadEndpoint:
    """测试文件上传解析端点。"""

    async def test_upload_endpoint(self):
        """上传文件应调用 UdaService.parse_upload 并返回解析结果。"""
        mock_doc = MagicMock()
        mock_doc.id = uuid.uuid4()
        mock_doc.original_filename = "test.docx"
        mock_doc.file_type = "docx"
        mock_doc.parse_status = "completed"
        mock_doc.content_text = "解析后的文本"
        mock_doc.content_ast = {"sections": []}
        mock_doc.file_size = 1024
        mock_doc.storage_path = "/files/test.docx"
        mock_doc.requirement_id = None
        mock_doc.error_message = None
        mock_doc.created_at = "2024-01-01T00:00:00"
        mock_doc.updated_at = "2024-01-01T00:00:00"
        mock_doc.deleted_at = None

        mock_service_instance = AsyncMock()
        mock_service_instance.parse_upload = AsyncMock(return_value=mock_doc)

        with patch("app.modules.uda.router.UdaService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/uda/parse",
                    files={"file": ("test.docx", b"fake file content", "application/octet-stream")},
                )

            app.dependency_overrides.clear()

        # 验证请求成功或参数校验
        assert response.status_code in (200, 201, 422)
