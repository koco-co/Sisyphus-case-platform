import uuid

from fastapi import APIRouter, Query, status

from app.core.dependencies import AsyncSessionDep
from app.modules.templates.schemas import (
    TemplateApplyRequest,
    TemplateApplyResponse,
    TemplateCreate,
    TemplateListItem,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdate,
)
from app.modules.templates.service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    session: AsyncSessionDep,
    category: str | None = None,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TemplateListResponse:
    svc = TemplateService(session)
    templates, total = await svc.list_templates(category, keyword, page, page_size)
    return TemplateListResponse(
        items=[TemplateListItem.model_validate(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: uuid.UUID, session: AsyncSessionDep) -> TemplateResponse:
    svc = TemplateService(session)
    tpl = await svc.get_template(template_id)
    return TemplateResponse.model_validate(tpl)


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(data: TemplateCreate, session: AsyncSessionDep) -> TemplateResponse:
    svc = TemplateService(session)
    tpl = await svc.create_template(data)
    return TemplateResponse.model_validate(tpl)


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    data: TemplateUpdate,
    session: AsyncSessionDep,
) -> TemplateResponse:
    svc = TemplateService(session)
    tpl = await svc.update_template(template_id, data)
    return TemplateResponse.model_validate(tpl)


@router.post("/{template_id}/apply", response_model=TemplateApplyResponse)
async def apply_template(
    template_id: uuid.UUID,
    data: TemplateApplyRequest,
    session: AsyncSessionDep,
) -> TemplateApplyResponse:
    """Apply a template with variable substitution to generate case content."""
    svc = TemplateService(session)
    result = await svc.apply_template(template_id, data.requirement_id, data.variables)
    return TemplateApplyResponse(**result)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: uuid.UUID, session: AsyncSessionDep) -> None:
    svc = TemplateService(session)
    await svc.soft_delete(template_id)
