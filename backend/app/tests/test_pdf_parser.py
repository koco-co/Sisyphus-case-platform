"""测试 PDF 解析器"""

import pytest

from app.plugins.pdf_parser import PDFParser


@pytest.mark.asyncio
async def test_pdf_parser_supports():
    """测试 PDF 解析器支持的格式"""
    parser = PDFParser()
    assert parser.supports(".pdf") is True
    assert parser.supports(".PDF") is True
    assert parser.supports(".md") is False


@pytest.mark.asyncio
async def test_pdf_parser_file_not_found():
    """测试文件不存在时抛出异常"""
    parser = PDFParser()

    with pytest.raises(FileNotFoundError):
        parser.parse("/nonexistent/file.pdf")
