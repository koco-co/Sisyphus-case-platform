"""B-M01-14 — 图片归档处理器单元测试"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestImageArchive:
    """测试图片归档到 MinIO。"""

    async def test_image_archive(self):
        """合法图片应归档到 MinIO 并返回路径。"""
        mock_minio = MagicMock()
        mock_minio.put_object = MagicMock()

        with (
            patch("app.engine.uda.image_handler.get_minio_client", return_value=mock_minio),
            patch("app.engine.uda.image_handler.ensure_bucket"),
        ):
            from app.engine.uda.image_handler import archive_image

            result = await archive_image(
                file_bytes=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
                original_filename="screenshot.png",
                requirement_id="req-001",
            )

        assert result.startswith("sisyphus-images/images/req-001/")
        assert result.endswith(".png")
        mock_minio.put_object.assert_called_once()

    async def test_image_archive_unsupported_format(self):
        """不支持的格式应抛出 ValueError。"""
        with (
            patch("app.engine.uda.image_handler.get_minio_client"),
            patch("app.engine.uda.image_handler.ensure_bucket"),
        ):
            from app.engine.uda.image_handler import archive_image

            with pytest.raises(ValueError, match="不支持的图片格式"):
                await archive_image(
                    file_bytes=b"data",
                    original_filename="test.exe",
                )

    async def test_image_archive_global_scope(self):
        """未提供 requirement_id 应使用 'global' 路径。"""
        mock_minio = MagicMock()
        mock_minio.put_object = MagicMock()

        with (
            patch("app.engine.uda.image_handler.get_minio_client", return_value=mock_minio),
            patch("app.engine.uda.image_handler.ensure_bucket"),
        ):
            from app.engine.uda.image_handler import archive_image

            result = await archive_image(
                file_bytes=b"\x89PNG" + b"\x00" * 50,
                original_filename="logo.png",
            )

        assert "global" in result


class TestExternalImageFetch:
    """测试外链图片抓取与替换。"""

    async def test_external_image_fetch(self):
        """Markdown 中的外链图片应被下载归档并替换 URL。"""
        md_content = "# 标题\n![logo](https://example.com/img.png)\n正文内容"
        mock_resp = MagicMock()
        mock_resp.content = b"\x89PNG" + b"\x00" * 50
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.engine.uda.image_handler.httpx.AsyncClient", return_value=mock_http),
            patch(
                "app.engine.uda.image_handler.archive_image",
                new_callable=AsyncMock,
                return_value="sisyphus-images/images/req/abc.png",
            ),
        ):
            from app.engine.uda.image_handler import fetch_and_archive_external_images

            result = await fetch_and_archive_external_images(md_content, "req-001")

        assert "https://example.com/img.png" not in result
        assert "/api/files/" in result

    async def test_no_external_images(self):
        """无外链图片时应返回原内容。"""
        md_content = "# 标题\n普通段落，没有图片"

        from app.engine.uda.image_handler import fetch_and_archive_external_images

        result = await fetch_and_archive_external_images(md_content)

        assert result == md_content
