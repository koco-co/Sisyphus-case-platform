"""B-M12-10 — Export API contract tests."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient


class TestExportExcelEndpoint:
    async def test_export_excel_endpoint_returns_xlsx_attachment(self):
        """GET /api/export/excel 应返回 workbench 导出按钮可下载的 xlsx 附件。"""
        requirement_id = uuid.uuid4()
        excel_bytes = b"PK\x03\x04mock-xlsx"
        mock_service_instance = AsyncMock()
        mock_service_instance.export_cases_excel = AsyncMock(return_value=excel_bytes)

        with patch("app.modules.export.router.ExportService", return_value=mock_service_instance):
            from app.core.database import get_async_session
            from app.main import app

            async def _override():
                yield AsyncMock()

            app.dependency_overrides[get_async_session] = _override
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get(f"/api/export/excel?requirement_id={requirement_id}")

            app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.content == excel_bytes
        assert resp.headers["content-disposition"] == "attachment; filename=test_cases.xlsx"
        assert (
            resp.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
