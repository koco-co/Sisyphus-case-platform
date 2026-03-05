"""文件上传 API"""

import os
import tempfile
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import File as FileModel
from app.schemas.file import FileResponse, FileUploadResponse
from app.services.storage import LocalStorage, get_storage

router = APIRouter(prefix="/api/files", tags=["files"])

# 解析器管理器（延迟导入，避免缺少依赖时报错）
_parser_manager = None


def get_parser_manager():
    """获取解析器管理器单例（延迟导入）"""
    global _parser_manager
    if _parser_manager is None:
        try:
            from app.plugins.manager import ParserManager

            _parser_manager = ParserManager()
        except ImportError:
            # 缺少依赖时返回 None
            pass
    return _parser_manager


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    upload_file: UploadFile = File(default=None),
    db: AsyncSession = Depends(get_db),
):
    """上传文件并解析内容"""
    if upload_file is None:
        raise HTTPException(400, "未提供文件")

    # 检查文件类型
    allowed_extensions = {".md", ".txt", ".pdf"}
    ext = (
        os.path.splitext(upload_file.filename)[1].lower()
        if upload_file.filename
        else ""
    )
    if ext not in allowed_extensions:
        raise HTTPException(400, f"不支持的文件类型: {ext}")

    # 读取文件内容
    content = await upload_file.read()

    # 检查文件大小 (10MB)
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(400, "文件大小不能超过 10MB")

    # 创建文件记录
    db_file = FileModel(
        filename=upload_file.filename or "unknown",
        original_name=upload_file.filename or "unknown",
        mime_type=upload_file.content_type,
        size=len(content),
    )
    db.add(db_file)
    await db.flush()

    # 保存文件到存储
    storage = get_storage()
    storage_path = await storage.save(
        db_file.id, content, upload_file.filename or "unknown"
    )

    db_file.storage_type = "local" if isinstance(storage, LocalStorage) else "minio"
    db_file.storage_path = storage_path

    # 解析文件内容
    parsed_content = ""
    try:
        parser_manager = get_parser_manager()
        if parser_manager:
            parser = parser_manager.get_parser(f"test{ext}")
            if parser:
                # 使用临时文件解析
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                    tmp_file.write(content)
                    tmp_path = tmp_file.name

                try:
                    parsed_content = parser.parse(tmp_path)
                    db_file.parsed_content = parsed_content
                finally:
                    os.unlink(tmp_path)
    except Exception:
        # 解析失败不影响上传
        parsed_content = ""
        db_file.parsed_content = None

    await db.commit()
    await db.refresh(db_file)

    return FileUploadResponse(
        file=FileResponse.model_validate(db_file),
        parsed_content=parsed_content,
    )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_info(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取文件信息"""
    try:
        uuid = UUID(file_id)
    except ValueError:
        raise HTTPException(400, "无效的文件 ID")

    result = await db.execute(select(FileModel).where(FileModel.id == uuid))
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(404, "文件不存在")

    return FileResponse.model_validate(file)


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """流式获取文件内容"""
    try:
        uuid = UUID(file_id)
    except ValueError:
        raise HTTPException(400, "无效的文件 ID")

    result = await db.execute(select(FileModel).where(FileModel.id == uuid))
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(404, "文件不存在")

    if not file.parsed_content:
        raise HTTPException(404, "文件内容不存在")

    async def generate():
        """分块流式返回内容"""
        chunk_size = 1024
        content = file.parsed_content or ""
        for i in range(0, len(content), chunk_size):
            yield content[i : i + chunk_size]

    return StreamingResponse(generate(), media_type="text/plain")
