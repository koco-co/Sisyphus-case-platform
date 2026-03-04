"""纯文本解析器"""

from typing import List

from app.plugins.base import DocumentParser


class TextParser(DocumentParser):
    """纯文本解析器"""

    def __init__(self) -> None:
        super().__init__()
        self.supported_extensions = [".txt", ".log", ".csv", ".json"]

    def supports(self, file_extension: str) -> bool:
        """支持的文件扩展名"""
        return file_extension.lower() in self.supported_extensions

    def parse(self, file_path: str) -> str:
        """
        解析纯文本文件

        Args:
            file_path: 文本文件路径

        Returns:
            文本内容

        Raises:
            FileNotFoundError: 文件不存在
        """
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 尝试不同的编码
        encodings = ["utf-8", "gbk", "gb2312", "latin-1"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        # 如果所有编码都失败，使用二进制模式读取
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")

    def parse_lines(self, file_path: str) -> List[str]:
        """
        按行解析文本文件

        Args:
            file_path: 文件路径

        Returns:
            文本行列表
        """
        text = self.parse(file_path)
        return text.split("\n")
