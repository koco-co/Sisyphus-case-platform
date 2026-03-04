"""文档解析器管理器"""

from pathlib import Path
from typing import List, Optional

from app.plugins.base import DocumentParser
from app.plugins.md_parser import MarkdownParser
from app.plugins.pdf_parser import PDFParser
from app.plugins.txt_parser import TextParser


class ParserManager:
    """文档解析器管理器"""

    def __init__(self) -> None:
        """初始化管理器，注册所有内置解析器"""
        self.parsers: List[DocumentParser] = [
            MarkdownParser(),
            PDFParser(),
            TextParser(),
            # 未来可以在这里添加更多解析器
            # WordParser(),
            # OCRParser(),
            # WebParser(),
        ]

    def register_parser(self, parser: DocumentParser) -> None:
        """
        注册新的解析器

        Args:
            parser: 解析器实例
        """
        self.parsers.append(parser)

    def get_parser(self, file_path: str) -> Optional[DocumentParser]:
        """
        根据文件路径获取合适的解析器

        Args:
            file_path: 文件路径

        Returns:
            解析器实例，如果不支持则返回 None
        """
        ext = Path(file_path).suffix

        for parser in self.parsers:
            if parser.supports(ext):
                return parser

        return None

    def parse_document(self, file_path: str) -> str:
        """
        自动选择合适的解析器解析文档

        Args:
            file_path: 文件路径

        Returns:
            提取的文本内容

        Raises:
            ValueError: 如果不支持的文件类型
            FileNotFoundError: 如果文件不存在
        """
        parser = self.get_parser(file_path)

        if not parser:
            ext = Path(file_path).suffix
            raise ValueError(
                f"不支持的文件类型: {ext}. " f"支持的类型: .md, .pdf, .txt"
            )

        return parser.parse(file_path)

    def get_supported_formats(self) -> List[str]:
        """
        获取所有支持的文件格式

        Returns:
            文件扩展名列表
        """
        formats: set = set()
        for parser in self.parsers:
            # 每个解析器可能支持多种格式
            # 这里简化处理，实际可以从解析器获取
            if hasattr(parser, "supported_extensions"):
                formats.update(parser.supported_extensions)
            else:
                # 根据解析器类名推断
                class_name = parser.__class__.__name__.lower()
                if "markdown" in class_name or "md" in class_name:
                    formats.update([".md", ".markdown"])
                elif "pdf" in class_name:
                    formats.add(".pdf")
                elif "text" in class_name or "txt" in class_name:
                    formats.update([".txt", ".log", ".csv"])

        return sorted(list(formats))
