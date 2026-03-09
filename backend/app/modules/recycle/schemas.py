import uuid

from app.shared.base_schema import BaseSchema


class RecycleItemResponse(BaseSchema):
    id: uuid.UUID
    entity_type: str
    name: str
    deleted_at: str


class RestoreRequest(BaseSchema):
    entity_type: str
    entity_id: uuid.UUID


class BatchRestoreRequest(BaseSchema):
    items: list[RestoreRequest]


class PermanentDeleteRequest(BaseSchema):
    entity_type: str
    entity_id: uuid.UUID
