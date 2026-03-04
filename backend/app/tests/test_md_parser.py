"""测试 Markdown 解析器"""

import os
import tempfile

import pytest

from app.plugins.md_parser import MarkdownParser


@pytest.mark.asyncio
async def test_markdown_parser():
    """测试 Markdown 解析器"""
    parser = MarkdownParser()

    # 创建临时 Markdown 文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# 测试标题\n\n这是测试内容")
        temp_path = f.name

    try:
        assert parser.supports(".md") is True
        assert parser.supports(".pdf") is False

        text = parser.parse(temp_path)
        assert "测试标题" in text
        assert "这是测试内容" in text
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_markdown_parser_markdown_extension():
    """测试 .markdown 扩展名"""
    parser = MarkdownParser()

    assert parser.supports(".markdown") is True
    assert parser.supports(".MD") is True


@pytest.mark.asyncio
async def test_markdown_parser_file_not_found():
    """测试文件不存在时抛出异常"""
    parser = MarkdownParser()

    with pytest.raises(FileNotFoundError):
        parser.parse("/nonexistent/file.md")


@pytest.mark.asyncio
async def test_markdown_extract_metadata():
    """测试提取 Markdown 元数据"""
    parser = MarkdownParser()

    # 创建带有标题的 Markdown 文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# 文档标题\n\n内容")
        temp_path = f.name

    try:
        metadata = parser.extract_metadata(temp_path)
        assert metadata.get("title") == "文档标题"
    finally:
        os.unlink(temp_path)
