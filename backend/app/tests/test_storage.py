"""测试文件存储服务"""

import pytest
from io import BytesIO
from uuid import uuid4

from app.services.storage import LocalStorage


@pytest.fixture
def local_storage(tmp_path):
    """创建临时本地存储"""
    return LocalStorage(base_path=str(tmp_path / "uploads"))


class TestLocalStorage:
    """本地存储测试"""

    @pytest.mark.asyncio
    async def test_save_and_read(self, local_storage):
        """测试保存和读取文件"""
        file_id = uuid4()
        content = b"test content for storage"
        file_data = BytesIO(content)

        storage_path = await local_storage.save(file_id, file_data, "test.txt")
        assert await local_storage.exists(storage_path)

        read_content = await local_storage.read(storage_path)
        assert read_content == content

    @pytest.mark.asyncio
    async def test_delete(self, local_storage):
        """测试删除文件"""
        file_id = uuid4()
        content = b"test content"
        file_data = BytesIO(content)

        storage_path = await local_storage.save(file_id, file_data, "test.txt")
        assert await local_storage.exists(storage_path)

        await local_storage.delete(storage_path)
        assert not await local_storage.exists(storage_path)

    @pytest.mark.asyncio
    async def test_exists_not_found(self, local_storage):
        """测试文件不存在"""
        assert not await local_storage.exists("/nonexistent/path/file.txt")

    @pytest.mark.asyncio
    async def test_hash_directory_structure(self, local_storage):
        """测试哈希目录结构"""
        file_id = uuid4()
        content = b"test content"
        file_data = BytesIO(content)

        storage_path = await local_storage.save(file_id, file_data, "test.txt")

        # 验证路径包含哈希前缀
        assert file_id.hex[:2] in storage_path
        assert file_id.hex in storage_path

    @pytest.mark.asyncio
    async def test_multiple_files_same_prefix(self, local_storage):
        """测试相同哈希前缀的多个文件"""
        # 创建两个具有相同哈希前缀的 UUID（模拟）
        file_id_1 = uuid4()
        file_id_2 = uuid4()

        content_1 = b"content 1"
        content_2 = b"content 2"

        storage_path_1 = await local_storage.save(
            file_id_1, BytesIO(content_1), "file1.txt"
        )
        storage_path_2 = await local_storage.save(
            file_id_2, BytesIO(content_2), "file2.txt"
        )

        # 验证两个文件都能正确读取
        assert await local_storage.read(storage_path_1) == content_1
        assert await local_storage.read(storage_path_2) == content_2

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, local_storage):
        """测试删除不存在的文件不应报错"""
        # 应该不会抛出异常
        await local_storage.delete("/nonexistent/path/file.txt")

    @pytest.mark.asyncio
    async def test_read_nonexistent_file_raises_error(self, local_storage):
        """测试读取不存在的文件应抛出异常"""
        with pytest.raises(FileNotFoundError):
            await local_storage.read("/nonexistent/path/file.txt")
