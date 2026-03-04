"""PDF 文档解析器"""

import pypdf

from app.plugins.base import DocumentParser


class PDFParser(DocumentParser):
    """PDF 文档解析器"""

    def supports(self, file_extension: str) -> bool:
        """支持的文件扩展名"""
        return file_extension.lower() == ".pdf"

    def parse(self, file_path: str) -> str:
        """
        解析 PDF 文件

        Args:
            file_path: PDF 文件路径

        Returns:
            提取的文本内容

        Raises:
            FileNotFoundError: 文件不存在
            RuntimeError: PDF 解析失败
        """
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                number_of_pages = len(reader.pages)

                for i in range(number_of_pages):
                    page = reader.pages[i]
                    text += page.extract_text() + "\n"

        except Exception as e:
            raise RuntimeError(f"PDF 解析失败: {str(e)}") from e

        return text

    def extract_metadata(self, file_path: str) -> dict:
        """
        提取 PDF 元数据

        Args:
            file_path: 文件路径

        Returns:
            元数据字典
        """
        metadata: dict = {}

        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                info = reader.metadata

                if info:
                    metadata["title"] = info.get("/Title", "")
                    metadata["author"] = info.get("/Author", "")
                    metadata["creator"] = info.get("/Creator", "")
                    metadata["producer"] = info.get("/Producer", "")

                metadata["pages"] = len(reader.pages)

        except Exception as e:
            metadata["error"] = str(e)

        return metadata
