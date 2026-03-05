"""文件存储服务 - 支持本地文件系统和 MinIO 混合存储"""

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import UUID


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def save(self, file_id: UUID, file_data: BinaryIO, filename: str) -> str:
        """保存文件，返回存储路径"""
        pass

    @abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """读取文件内容"""
        pass

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """删除文件"""
        pass

    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """检查文件是否存在"""
        pass


class LocalStorage(StorageBackend):
    """本地文件系统存储"""

    def __init__(self, base_path: str = "./uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, file_id: UUID, file_data: BinaryIO, filename: str) -> str:
        # 按前两位 hash 组织目录
        subdir = self.base_path / file_id.hex[:2]
        subdir.mkdir(parents=True, exist_ok=True)

        storage_path = subdir / f"{file_id.hex}_{filename}"
        with open(storage_path, "wb") as f:
            shutil.copyfileobj(file_data, f)

        return str(storage_path)

    async def read(self, storage_path: str) -> bytes:
        with open(storage_path, "rb") as f:
            return f.read()

    async def delete(self, storage_path: str) -> None:
        Path(storage_path).unlink(missing_ok=True)

    async def exists(self, storage_path: str) -> bool:
        return Path(storage_path).exists()


class MinioStorage(StorageBackend):
    """MinIO 对象存储"""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ):
        from minio import Minio

        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self.bucket = bucket
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    async def save(self, file_id: UUID, file_data: BinaryIO, filename: str) -> str:
        object_name = f"{file_id.hex}/{filename}"
        file_data.seek(0, 2)
        size = file_data.tell()
        file_data.seek(0)

        self.client.put_object(self.bucket, object_name, file_data, size)
        return object_name

    async def read(self, storage_path: str) -> bytes:
        response = self.client.get_object(self.bucket, storage_path)
        return response.read()

    async def delete(self, storage_path: str) -> None:
        self.client.remove_object(self.bucket, storage_path)

    async def exists(self, storage_path: str) -> bool:
        try:
            self.client.stat_object(self.bucket, storage_path)
            return True
        except Exception:
            return False


def get_storage_backend() -> StorageBackend:
    """根据配置获取存储后端"""
    from app.config import settings

    storage_type = getattr(settings, "STORAGE_TYPE", "local")

    if storage_type == "minio":
        return MinioStorage(
            endpoint=getattr(settings, "MINIO_ENDPOINT", "localhost:9000"),
            access_key=getattr(settings, "MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=getattr(settings, "MINIO_SECRET_KEY", "minioadmin"),
            bucket=getattr(settings, "MINIO_BUCKET", "sisyphus"),
            secure=getattr(settings, "MINIO_SECURE", False),
        )
    else:
        return LocalStorage(
            base_path=getattr(settings, "UPLOAD_PATH", "./uploads")
        )


# 全局存储实例（延迟初始化）
_storage: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """获取存储实例（单例）"""
    global _storage
    if _storage is None:
        _storage = get_storage_backend()
    return _storage
