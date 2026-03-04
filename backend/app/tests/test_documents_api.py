"""测试文档解析 API"""

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_parse_document():
    """测试文档解析 API"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Document\n\nThis is test content.")
            temp_path = f.name

        try:
            # 使用文件上传
            with open(temp_path, "rb") as f:
                response = await ac.post(
                    "/api/documents/parse",
                    files={"file": ("test.md", f, "text/markdown")},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Test Document" in data["text"]
        finally:
            os.unlink(temp_path)


@pytest.mark.asyncio
async def test_get_supported_formats():
    """测试获取支持的格式 API"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/documents/formats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert ".md" in data["formats"]
        assert ".pdf" in data["formats"]
        assert ".txt" in data["formats"]


@pytest.mark.asyncio
async def test_parse_unsupported_format():
    """测试不支持的文件格式"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # 创建不支持的文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                response = await ac.post(
                    "/api/documents/parse",
                    files={"file": ("test.xyz", f, "application/octet-stream")},
                )

            assert response.status_code == 400
        finally:
            os.unlink(temp_path)
