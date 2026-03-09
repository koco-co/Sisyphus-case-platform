import uuid
from datetime import datetime
from typing import Literal

from app.shared.base_schema import BaseResponse, BaseSchema


class TestPointCreate(BaseSchema):
    group_name: str
    title: str
    description: str | None = None
    priority: str = "P1"
    estimated_cases: int = 3
    source: str | None = "user_added"


class TestPointUpdate(BaseSchema):
    group_name: str | None = None
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    estimated_cases: int | None = None


class TestPointResponse(BaseResponse):
    scene_map_id: uuid.UUID
    group_name: str
    title: str
    description: str | None
    priority: str
    status: str
    estimated_cases: int
    source: str


class SceneMapResponse(BaseResponse):
    requirement_id: uuid.UUID
    status: str
    confirmed_at: datetime | None
    test_points: list[TestPointResponse] = []


# ── Batch operations (B-M04-09) ───────────────────────────────────


class BatchPointUpdate(BaseSchema):
    id: uuid.UUID
    group_name: str | None = None
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    estimated_cases: int | None = None


class BatchUpdateRequest(BaseSchema):
    updates: list[BatchPointUpdate]


class ReorderItem(BaseSchema):
    id: uuid.UUID
    sort_order: int


class ReorderRequest(BaseSchema):
    order: list[ReorderItem]


# ── Export (B-M04-10) ─────────────────────────────────────────────

ExportFormatLiteral = Literal["json", "md"]
