"""测试文档解析器管理器"""

import os
import tempfile

import pytest

from app.plugins.manager import ParserManager


@pytest.mark.asyncio
async def test_parser_manager():
    """测试插件管理器"""
    manager = ParserManager()

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test")
        md_path = f.name

    try:
        # 测试获取解析器
        parser = manager.get_parser(md_path)
        assert parser is not None
        assert parser.supports(".md") is True

        # 测试解析
        text = manager.parse_document(md_path)
        assert "Test" in text
    finally:
        os.unlink(md_path)


@pytest.mark.asyncio
async def test_parser_manager_unsupported_format():
    """测试不支持的格式"""
    manager = ParserManager()

    # 创建不支持的文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False) as f:
        f.write("test")
        temp_path = f.name

    try:
        with pytest.raises(ValueError) as exc_info:
            manager.parse_document(temp_path)
        assert "不支持的文件类型" in str(exc_info.value)
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_parser_manager_get_supported_formats():
    """测试获取支持的格式"""
    manager = ParserManager()

    formats = manager.get_supported_formats()
    assert ".md" in formats
    assert ".pdf" in formats
    assert ".txt" in formats
