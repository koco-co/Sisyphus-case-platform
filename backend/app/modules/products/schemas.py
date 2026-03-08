import uuid

from app.shared.base_schema import BaseResponse, BaseSchema


class ProductCreate(BaseSchema):
    name: str
    slug: str
    description: str | None = None


class ProductResponse(BaseResponse):
    name: str
    slug: str
    description: str | None


class IterationCreate(BaseSchema):
    product_id: uuid.UUID
    name: str
    start_date: str | None = None
    end_date: str | None = None


class IterationResponse(BaseResponse):
    product_id: uuid.UUID
    name: str
    start_date: str | None
    end_date: str | None
    status: str


class RequirementCreate(BaseSchema):
    iteration_id: uuid.UUID
    req_id: str
    title: str
    content_ast: dict | None = None
    frontmatter: dict | None = None


class RequirementResponse(BaseResponse):
    iteration_id: uuid.UUID
    req_id: str
    title: str
    status: str
    version: int
