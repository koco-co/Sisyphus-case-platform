import uuid
from datetime import datetime

from app.shared.base_schema import BaseSchema


class SearchResultItem(BaseSchema):
    id: uuid.UUID
    entity_type: str
    title: str
    summary: str | None = None
    updated_at: datetime | None = None


class SearchResponse(BaseSchema):
    items: list[SearchResultItem]
    total: int
    page: int
    page_size: int
