"""T-UNIT-03 — UDA 解析器单元测试（纯函数，不依赖数据库）"""

from __future__ import annotations

from app.engine.uda.ast_types import ASTNode, DocumentAST, NodeType


# ═══════════════════════════════════════════════════════════════════
# Markdown 解析器
# ═══════════════════════════════════════════════════════════════════


class TestMarkdownParser:
    def test_parse_markdown_basic(self):
        from app.modules.uda.parsers.md_parser import parse_markdown

        md = b"# Title\nSome content\n## Subtitle\nMore content"
        full_text, ast = parse_markdown(md)

        assert "Title" in full_text
        assert "Subtitle" in full_text
        assert len(ast["sections"]) == 2
        assert ast["sections"][0]["heading"] == "Title"
        assert ast["sections"][1]["heading"] == "Subtitle"

    def test_parse_markdown_preserves_body(self):
        from app.modules.uda.parsers.md_parser import parse_markdown

        md = b"# Header\nLine 1\nLine 2\nLine 3"
        _, ast = parse_markdown(md)

        body = ast["sections"][0]["body"]
        assert "Line 1" in body
        assert "Line 2" in body
        assert "Line 3" in body

    def test_parse_markdown_empty(self):
        from app.modules.uda.parsers.md_parser import parse_markdown

        _, ast = parse_markdown(b"")
        assert ast["sections"] == []
        assert ast["raw_text"] == ""

    def test_parse_markdown_no_heading(self):
        from app.modules.uda.parsers.md_parser import parse_markdown

        md = b"Just plain text without headings."
        full_text, ast = parse_markdown(md)

        assert full_text == "Just plain text without headings."
        assert len(ast["sections"]) == 1
        assert ast["sections"][0]["heading"] == ""

    def test_parse_markdown_multiple_levels(self):
        from app.modules.uda.parsers.md_parser import parse_markdown

        md = b"# H1\nP1\n## H2\nP2\n### H3\nP3"
        _, ast = parse_markdown(md)

        assert len(ast["sections"]) == 3
        assert ast["sections"][0]["heading"] == "H1"
        assert ast["sections"][1]["heading"] == "H2"
        assert ast["sections"][2]["heading"] == "H3"


# ═══════════════════════════════════════════════════════════════════
# TXT 解析器
# ═══════════════════════════════════════════════════════════════════


class TestTxtParser:
    def test_parse_txt_basic(self):
        from app.modules.uda.parsers.txt_parser import parse_txt

        text = b"Hello World"
        full_text, ast = parse_txt(text)

        assert full_text == "Hello World"
        assert ast["raw_text"] == "Hello World"
        assert len(ast["sections"]) == 1
        assert ast["sections"][0]["heading"] == ""
        assert ast["sections"][0]["body"] == "Hello World"

    def test_parse_txt_utf8(self):
        from app.modules.uda.parsers.txt_parser import parse_txt

        text = "需求文档：数据同步功能".encode("utf-8")
        full_text, ast = parse_txt(text)

        assert "数据同步功能" in full_text

    def test_parse_txt_empty(self):
        from app.modules.uda.parsers.txt_parser import parse_txt

        full_text, ast = parse_txt(b"")
        assert full_text == ""
        assert ast["sections"][0]["body"] == ""


# ═══════════════════════════════════════════════════════════════════
# AST → Markdown 转换
# ═══════════════════════════════════════════════════════════════════


class TestAstToMarkdown:
    def test_heading_node(self):
        doc = DocumentAST(
            title="Test",
            source_type="md",
            nodes=[ASTNode(type=NodeType.HEADING, content="Hello", level=2)],
        )
        md = doc.to_markdown()
        assert md == "## Hello"

    def test_paragraph_node(self):
        doc = DocumentAST(
            nodes=[ASTNode(type=NodeType.PARAGRAPH, content="Some text")]
        )
        md = doc.to_markdown()
        assert md == "Some text"

    def test_list_node(self):
        doc = DocumentAST(
            nodes=[
                ASTNode(
                    type=NodeType.LIST,
                    children=[
                        ASTNode(type=NodeType.LIST_ITEM, content="Item A"),
                        ASTNode(type=NodeType.LIST_ITEM, content="Item B"),
                    ],
                )
            ]
        )
        md = doc.to_markdown()
        assert "- Item A" in md
        assert "- Item B" in md

    def test_code_block_node(self):
        doc = DocumentAST(
            nodes=[ASTNode(type=NodeType.CODE_BLOCK, content="print('hi')", language="python")]
        )
        md = doc.to_markdown()
        assert "```python" in md
        assert "print('hi')" in md

    def test_image_node(self):
        doc = DocumentAST(
            nodes=[ASTNode(type=NodeType.IMAGE, url="http://img.png", alt="pic")]
        )
        md = doc.to_markdown()
        assert "![pic](http://img.png)" in md

    def test_blockquote_node(self):
        doc = DocumentAST(
            nodes=[ASTNode(type=NodeType.BLOCKQUOTE, content="quoted")]
        )
        md = doc.to_markdown()
        assert "> quoted" in md

    def test_hr_node(self):
        doc = DocumentAST(nodes=[ASTNode(type=NodeType.HORIZONTAL_RULE)])
        md = doc.to_markdown()
        assert "---" in md

    def test_mixed_nodes(self):
        doc = DocumentAST(
            nodes=[
                ASTNode(type=NodeType.HEADING, content="Title", level=1),
                ASTNode(type=NodeType.PARAGRAPH, content="Body text"),
                ASTNode(type=NodeType.HORIZONTAL_RULE),
            ]
        )
        md = doc.to_markdown()
        assert "# Title" in md
        assert "Body text" in md
        assert "---" in md

    def test_empty_document(self):
        doc = DocumentAST()
        md = doc.to_markdown()
        assert md == ""
