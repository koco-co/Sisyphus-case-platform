import uuid
from datetime import datetime

from app.shared.base_schema import BaseSchema


class AuditLogCreate(BaseSchema):
    user_id: uuid.UUID | None = None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None = None
    old_value: dict | None = None
    new_value: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class AuditLogResponse(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    old_value: dict | None
    new_value: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
