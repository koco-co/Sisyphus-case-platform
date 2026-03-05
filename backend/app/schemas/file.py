"""文件相关的 Pydantic Schema"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class FileBase(BaseModel):
    """文件基础 Schema"""

    original_name: str
    mime_type: Optional[str] = None
    size: Optional[int] = None


class FileCreate(FileBase):
    """文件创建 Schema"""

    pass


class FileResponse(FileBase):
    """文件响应 Schema"""

    id: UUID
    filename: str
    storage_type: str
    storage_path: Optional[str] = None
    parsed_content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """文件上传响应 Schema"""

    file: FileResponse
    parsed_content: str  # 解析后的内容
