"""测试文档解析器基类"""

import pytest

from app.plugins.base import DocumentParser


class ConcreteParser(DocumentParser):
    """具体解析器实现用于测试"""

    def parse(self, file_path: str) -> str:
        return "test content"

    def supports(self, file_extension: str) -> bool:
        return file_extension == ".test"


def test_parser_validate_file():
    """测试文件验证方法"""
    parser = ConcreteParser()

    # 测试不存在的文件
    assert parser.validate_file("nonexistent.txt") is False


def test_parser_validate_existing_file():
    """测试存在的文件验证"""
    import tempfile

    parser = ConcreteParser()

    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
        f.write(b"test")

    assert parser.validate_file(temp_path) is True

    # 清理
    import os

    os.unlink(temp_path)


def test_parser_cannot_instantiate_abstract():
    """测试抽象类不能直接实例化"""
    with pytest.raises(TypeError):
        DocumentParser()
