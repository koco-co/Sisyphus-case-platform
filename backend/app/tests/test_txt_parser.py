"""测试纯文本解析器"""

import os
import tempfile

import pytest

from app.plugins.txt_parser import TextParser


@pytest.mark.asyncio
async def test_text_parser():
    """测试纯文本解析器"""
    parser = TextParser()

    # 创建临时文本文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("这是测试文本内容")
        temp_path = f.name

    try:
        assert parser.supports(".txt") is True
        text = parser.parse(temp_path)
        assert "这是测试文本内容" in text
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_text_parser_extensions():
    """测试文本解析器支持的扩展名"""
    parser = TextParser()

    assert parser.supports(".txt") is True
    assert parser.supports(".log") is True
    assert parser.supports(".csv") is True
    assert parser.supports(".json") is True
    assert parser.supports(".pdf") is False


@pytest.mark.asyncio
async def test_text_parser_file_not_found():
    """测试文件不存在时抛出异常"""
    parser = TextParser()

    with pytest.raises(FileNotFoundError):
        parser.parse("/nonexistent/file.txt")


@pytest.mark.asyncio
async def test_text_parser_parse_lines():
    """测试按行解析"""
    parser = TextParser()

    # 创建多行文本文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("第一行\n第二行\n第三行")
        temp_path = f.name

    try:
        lines = parser.parse_lines(temp_path)
        assert len(lines) == 3
        assert lines[0] == "第一行"
    finally:
        os.unlink(temp_path)
