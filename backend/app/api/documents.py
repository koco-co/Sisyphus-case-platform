"""文档解析 API"""

import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.plugins.manager import ParserManager

router = APIRouter(prefix="/api/documents", tags=["documents"])

parser_manager = ParserManager()


@router.post("/parse")
async def parse_document(file: UploadFile = File(...)):
    """
    解析上传的文档

    Args:
        file: 上传的文件

    Returns:
        解析结果

    Raises:
        HTTPException: 400 不支持的文件类型，500 解析失败
    """
    # 验证文件扩展名
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""

    if not parser_manager.get_parser(f"test{file_ext}"):
        raise HTTPException(
            status_code=400, detail=f"不支持的文件类型: {file_ext}"
        )

    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 解析文档
        text = parser_manager.parse_document(tmp_path)

        return {
            "success": True,
            "filename": file.filename,
            "text": text,
            "length": len(text),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/formats")
async def get_supported_formats():
    """
    获取支持的文件格式列表

    Returns:
        文件格式列表
    """
    formats = parser_manager.get_supported_formats()

    return {"success": True, "formats": formats, "count": len(formats)}
