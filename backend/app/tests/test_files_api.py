"""测试文件上传 API"""

import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_upload_file_success():
    """测试成功上传文件"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Document\n\nThis is test content for upload.")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                response = await ac.post(
                    "/api/files/upload",
                    files={"file": ("test.md", f, "text/markdown")},
                )

            assert response.status_code == 200
            data = response.json()
            assert "file" in data
            assert "parsed_content" in data
            assert data["file"]["original_name"] == "test.md"
            assert "Test Document" in data["parsed_content"]
        finally:
            os.unlink(temp_path)


@pytest.mark.asyncio
async def test_upload_unsupported_file_type():
    """测试上传不支持的文件类型"""
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
                    "/api/files/upload",
                    files={"file": ("test.xyz", f, "application/octet-stream")},
                )

            assert response.status_code == 400
        finally:
            os.unlink(temp_path)


@pytest.mark.asyncio
async def test_upload_txt_file():
    """测试上传文本文件"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a plain text file.\nLine 2\nLine 3")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                response = await ac.post(
                    "/api/files/upload",
                    files={"file": ("test.txt", f, "text/plain")},
                )

            assert response.status_code == 200
            data = response.json()
            assert "plain text file" in data["parsed_content"]
        finally:
            os.unlink(temp_path)


@pytest.mark.asyncio
async def test_get_file_info_not_found():
    """测试获取不存在的文件信息"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(
            "/api/files/00000000-0000-0000-0000-000000000000"
        )

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_file_info_invalid_uuid():
    """测试获取文件信息时使用无效的 UUID"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/files/invalid-uuid")

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_file_content_not_found():
    """测试获取不存在文件的内容"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(
            "/api/files/00000000-0000-0000-0000-000000000000/content"
        )

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_and_retrieve_file():
    """测试上传文件后获取内容和信息"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # 上传文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Integration Test\n\nTesting full workflow.")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                upload_response = await ac.post(
                    "/api/files/upload",
                    files={"file": ("integration.md", f, "text/markdown")},
                )

            assert upload_response.status_code == 200
            upload_data = upload_response.json()
            file_id = upload_data["file"]["id"]

            # 获取文件信息
            info_response = await ac.get(f"/api/files/{file_id}")
            assert info_response.status_code == 200
            info_data = info_response.json()
            assert info_data["original_name"] == "integration.md"

            # 获取文件内容
            content_response = await ac.get(f"/api/files/{file_id}/content")
            assert content_response.status_code == 200
            content = content_response.text
            assert "Integration Test" in content
        finally:
            os.unlink(temp_path)
