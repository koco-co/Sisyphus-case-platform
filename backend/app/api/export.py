"""用例导出 API"""

import json
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.export import ExportService
from ..models import ExportTemplate

router = APIRouter(prefix="/api/export", tags=["export"])


# Schemas
class FieldConfig(BaseModel):
    fields: List[str] = ["title", "priority", "preconditions", "steps"]


class FormatConfig(BaseModel):
    delimiter: str = ","
    include_headers: bool = True


class FilterConfig(BaseModel):
    priority: Optional[List[str]] = None


class TemplateCreate(BaseModel):
    name: str
    field_config: Optional[FieldConfig] = None
    format_config: Optional[FormatConfig] = None
    filter_config: Optional[FilterConfig] = None
    is_default: bool = False


class TemplateResponse(BaseModel):
    id: UUID
    name: str
    field_config: dict
    format_config: dict
    filter_config: dict
    is_default: bool
    created_at: str

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    test_case_ids: List[str]
    format: str = "csv"  # csv or json
    template_id: Optional[str] = None
    field_config: Optional[FieldConfig] = None
    format_config: Optional[FormatConfig] = None


# Default template
DEFAULT_TEMPLATE = {
    "name": "默认模板",
    "field_config": {
        "fields": ["title", "priority", "preconditions", "steps", "tags"]
    },
    "format_config": {
        "delimiter": ",",
        "include_headers": True
    },
    "filter_config": {},
    "is_default": True,
}


# Endpoints
@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    """获取导出模板列表"""
    service = ExportService(db)
    templates = await service.get_templates()

    # 如果没有模板，返回默认模板
    if not templates:
        return [TemplateResponse(
            id=UUID("00000000-0000-0000-0000-000000000000"),
            **DEFAULT_TEMPLATE,
            created_at=""
        )]

    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建导出模板"""
    service = ExportService(db)

    template_data = {
        "name": data.name,
        "field_config": data.field_config.model_dump() if data.field_config else {},
        "format_config": data.format_config.model_dump() if data.format_config else {},
        "filter_config": data.filter_config.model_dump() if data.filter_config else {},
        "is_default": data.is_default,
    }

    template = await service.create_template(template_data)
    return TemplateResponse.model_validate(template)


@router.post("/")
async def export_test_cases(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
):
    """导出测试用例"""
    service = ExportService(db)

    # 获取或创建模板配置
    template = None
    if request.template_id and request.template_id != "00000000-0000-0000-0000-000000000000":
        result = await db.execute(
            select(ExportTemplate).where(ExportTemplate.id == request.template_id)
        )
        template = result.scalar_one_or_none()

    # 如果没有模板，使用请求中的配置或默认配置
    if not template:
        template = ExportTemplate(
            name="临时模板",
            field_config=request.field_config.model_dump() if request.field_config else DEFAULT_TEMPLATE["field_config"],
            format_config=request.format_config.model_dump() if request.format_config else DEFAULT_TEMPLATE["format_config"],
            filter_config={},
            is_default=False,
        )

    # 转换 ID
    try:
        test_case_ids = [UUID(tc_id) for tc_id in request.test_case_ids]
    except ValueError as e:
        raise HTTPException(400, f"无效的测试用例 ID: {e}")

    # 根据格式导出
    if request.format == "json":
        content = await service.export_json(test_case_ids, template)
        return JSONResponse(
            content=content,
            headers={
                "Content-Disposition": "attachment; filename=test_cases.json"
            },
        )
    else:
        content = await service.export_csv(test_case_ids, template)
        return PlainTextResponse(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=test_cases.csv"
            },
        )


@router.get("/fields")
async def get_available_fields():
    """获取可导出的字段列表"""
    return {
        "fields": [
            {"key": "title", "label": "用例标题", "required": True},
            {"key": "priority", "label": "优先级"},
            {"key": "preconditions", "label": "前置条件"},
            {"key": "steps", "label": "测试步骤"},
            {"key": "tags", "label": "标签"},
            {"key": "requirement_id", "label": "关联需求"},
            {"key": "created_at", "label": "创建时间"},
            {"key": "updated_at", "label": "更新时间"},
        ]
    }
