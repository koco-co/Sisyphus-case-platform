"""PDF 解析器单元测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.modules.uda.parsers.pdf_parser import parse_pdf


class TestPdfParser:
    def test_parse_pdf_extracts_pages_and_sections(self):
        """PDF 文本应按页拼接，并识别编号标题为 section heading。"""
        page1 = MagicMock()
        page1.extract_text.return_value = "1 概述\n系统支持目录发布流程。"
        page2 = MagicMock()
        page2.extract_text.return_value = "2 约束\n发布前需要完成审批。"

        reader = MagicMock()
        reader.pages = [page1, page2]

        with patch("app.modules.uda.parsers.pdf_parser.PdfReader", return_value=reader):
            full_text, ast = parse_pdf(b"%PDF-mock")

        assert full_text == "1 概述\n系统支持目录发布流程。\n\n2 约束\n发布前需要完成审批。"
        assert ast["page_count"] == 2
        assert ast["sections"] == [
            {"heading": "1 概述", "body": "系统支持目录发布流程。"},
            {"heading": "2 约束", "body": "发布前需要完成审批。"},
        ]

    def test_parse_pdf_handles_empty_page_text(self):
        """当页面无可提取文本时应返回空 sections。"""
        page = MagicMock()
        page.extract_text.return_value = None
        reader = MagicMock()
        reader.pages = [page]

        with patch("app.modules.uda.parsers.pdf_parser.PdfReader", return_value=reader):
            full_text, ast = parse_pdf(b"%PDF-empty")

        assert full_text == ""
        assert ast["page_count"] == 1
        assert ast["sections"] == []
