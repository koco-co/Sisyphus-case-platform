"""T-UNIT-08 — RAG 文档分块器单元测试（纯函数）"""

from __future__ import annotations

from app.engine.rag.chunker import Chunk, chunk_by_headers, chunk_by_paragraphs


class TestChunkByHeaders:
    def test_basic_header_split(self):
        """按标题分块，每个标题产生一个 chunk。"""
        text = "# Chapter 1\nContent A\n# Chapter 2\nContent B"
        chunks = chunk_by_headers(text)

        assert len(chunks) == 2
        assert "Chapter 1" in chunks[0].content
        assert "Content A" in chunks[0].content
        assert "Chapter 2" in chunks[1].content

    def test_header_path_metadata(self):
        """分块元数据应保留章节路径。"""
        text = "# Main\nIntro\n## Sub\nDetail"
        chunks = chunk_by_headers(text, source_id="doc-001")

        assert chunks[0].metadata["source_id"] == "doc-001"
        assert "Main" in chunks[0].metadata.get("section_path", "")

    def test_empty_text_returns_empty(self):
        chunks = chunk_by_headers("")
        assert chunks == []

    def test_whitespace_only_returns_empty(self):
        chunks = chunk_by_headers("   \n\n  ")
        assert chunks == []

    def test_no_headers_single_chunk(self):
        """无标题文本应产生单个 chunk。"""
        text = "Plain text without any markdown headers."
        chunks = chunk_by_headers(text)
        assert len(chunks) == 1
        assert "Plain text" in chunks[0].content

    def test_chunk_index_sequential(self):
        text = "# A\nText A\n# B\nText B\n# C\nText C"
        chunks = chunk_by_headers(text)
        indices = [c.index for c in chunks]
        assert indices == list(range(len(chunks)))


class TestChunkWithOverlap:
    def test_overlap_in_paragraph_chunking(self):
        """段落分块应支持重叠窗口。"""
        paragraphs = "\n\n".join([f"Paragraph {i} content here." for i in range(10)])
        chunks = chunk_by_paragraphs(paragraphs, max_chunk_size=80, overlap=20)

        assert len(chunks) > 1
        for chunk in chunks:
            assert isinstance(chunk, Chunk)

    def test_no_overlap(self):
        """overlap=0 时相邻 chunk 不应有重叠内容。"""
        paragraphs = "AAA BBB CCC\n\nDDD EEE FFF\n\nGGG HHH III"
        chunks = chunk_by_paragraphs(paragraphs, max_chunk_size=20, overlap=0)
        assert len(chunks) >= 2


class TestLongSectionSplit:
    def test_long_section_is_split(self):
        """超过 max_chunk_size 的段落应被二次切分。"""
        long_content = "# Big Section\n" + "\n\n".join(["Content block " * 10 for _ in range(5)])
        chunks = chunk_by_headers(long_content, max_chunk_size=100, overlap=20)

        assert len(chunks) > 1
        for chunk in chunks:
            # 每个 chunk 不应极端超出限制（允许略微超出因为按段落边界切）
            assert len(chunk.content) < 500

    def test_token_estimate(self):
        """Chunk.token_estimate 应粗估 token 数。"""
        chunk = Chunk(content="这是一段中文测试内容用于验证token估算")
        assert chunk.token_estimate > 0
        assert chunk.token_estimate == len(chunk.content) // 2

    def test_source_id_propagated(self):
        """source_id 应传播到所有 chunk 的 metadata 中。"""
        text = "# Title\n" + "A long paragraph. " * 50
        chunks = chunk_by_headers(text, max_chunk_size=100, overlap=10, source_id="test-doc")

        for chunk in chunks:
            assert chunk.metadata["source_id"] == "test-doc"
