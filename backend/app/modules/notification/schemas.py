import uuid

from app.shared.base_schema import BaseResponse, BaseSchema


class NotificationCreate(BaseSchema):
    user_id: uuid.UUID
    title: str
    content: str | None = None
    notification_type: str = "system"
    related_type: str | None = None
    related_id: uuid.UUID | None = None


class NotificationResponse(BaseResponse):
    user_id: uuid.UUID
    title: str
    content: str | None
    notification_type: str
    is_read: bool
    related_type: str | None
    related_id: uuid.UUID | None


class UnreadCountResponse(BaseSchema):
    count: int
