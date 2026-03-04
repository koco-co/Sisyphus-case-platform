"""文档解析器抽象基类"""

from abc import ABC, abstractmethod
from pathlib import Path


class DocumentParser(ABC):
    """文档解析器抽象基类"""

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        解析文档，返回纯文本

        Args:
            file_path: 文档路径

        Returns:
            提取的文本内容
        """
        pass

    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        """
        判断是否支持该文件类型

        Args:
            file_extension: 文件扩展名（如 .pdf, .md）

        Returns:
            是否支持
        """
        pass

    def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否存在且可读

        Args:
            file_path: 文件路径

        Returns:
            文件是否有效
        """
        path = Path(file_path)
        return path.exists() and path.is_file()
