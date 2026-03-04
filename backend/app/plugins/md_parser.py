"""Markdown 文档解析器"""

from app.plugins.base import DocumentParser


class MarkdownParser(DocumentParser):
    """Markdown 文档解析器"""

    def supports(self, file_extension: str) -> bool:
        """支持的文件扩展名"""
        return file_extension.lower() in [".md", ".markdown"]

    def parse(self, file_path: str) -> str:
        """
        解析 Markdown 文件

        Args:
            file_path: Markdown 文件路径

        Returns:
            文本内容

        Raises:
            FileNotFoundError: 文件不存在
        """
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def extract_metadata(self, file_path: str) -> dict:
        """
        提取 Markdown 元数据（如标题、作者等）

        Args:
            file_path: 文件路径

        Returns:
            元数据字典
        """
        content = self.parse(file_path)
        lines = content.split("\n")

        metadata: dict = {}
        for line in lines:
            if line.startswith("# "):
                metadata["title"] = line[2:].strip()
                break
            elif line.startswith("title:"):
                metadata["title"] = line.split(":", 1)[1].strip()

        return metadata
