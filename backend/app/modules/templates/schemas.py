import uuid

from app.shared.base_schema import BaseResponse, BaseSchema


class TemplateCreate(BaseSchema):
    name: str
    category: str = "functional"
    description: str | None = None
    template_content: dict = {}
    variables: dict | None = None
    is_builtin: bool = False
    created_by: uuid.UUID | None = None


class TemplateUpdate(BaseSchema):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    template_content: dict | None = None
    variables: dict | None = None
    status: str | None = None


class TemplateResponse(BaseResponse):
    name: str
    category: str
    description: str | None
    template_content: dict
    variables: dict | None
    usage_count: int
    is_builtin: bool
    created_by: uuid.UUID | None
    status: str


class TemplateListItem(BaseResponse):
    name: str
    category: str
    description: str | None
    usage_count: int
    is_builtin: bool
    status: str


class TemplateListResponse(BaseSchema):
    items: list[TemplateListItem]
    total: int
    page: int
    page_size: int


class TemplateApplyRequest(BaseSchema):
    requirement_id: uuid.UUID
    variables: dict | None = None


class TemplateApplyResponse(BaseSchema):
    template_id: uuid.UUID
    applied_content: dict
