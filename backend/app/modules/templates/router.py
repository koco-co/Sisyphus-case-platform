import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel as PydanticBaseModel

from app.core.dependencies import AsyncSessionDep
from app.modules.templates.service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateCreate(PydanticBaseModel):
    name: str
    category: str = "functional"
    description: str | None = None
    template_content: dict = {}
    variables: dict | None = None


@router.get("/")
async def list_templates(
    session: AsyncSessionDep,
    category: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    svc = TemplateService(session)
    templates, total = await svc.list_templates(category, page, page_size)
    return {
        "items": [
            {
                "id": str(t.id),
                "name": t.name,
                "category": t.category,
                "description": t.description,
                "usage_count": t.usage_count,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else "",
            }
            for t in templates
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{template_id}")
async def get_template(template_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = TemplateService(session)
    tpl = await svc.get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return {
        "id": str(tpl.id),
        "name": tpl.name,
        "category": tpl.category,
        "description": tpl.description,
        "template_content": tpl.template_content,
        "variables": tpl.variables,
        "usage_count": tpl.usage_count,
        "status": tpl.status,
    }


@router.post("/", status_code=201)
async def create_template(data: TemplateCreate, session: AsyncSessionDep) -> dict:
    svc = TemplateService(session)
    tpl = await svc.create_template(
        name=data.name,
        category=data.category,
        description=data.description,
        template_content=data.template_content,
        variables=data.variables,
    )
    return {"id": str(tpl.id), "name": tpl.name}


@router.post("/{template_id}/use")
async def use_template(template_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = TemplateService(session)
    tpl = await svc.use_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"id": str(tpl.id), "template_content": tpl.template_content, "variables": tpl.variables}


@router.delete("/{template_id}")
async def delete_template(template_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = TemplateService(session)
    success = await svc.soft_delete(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"ok": True}
