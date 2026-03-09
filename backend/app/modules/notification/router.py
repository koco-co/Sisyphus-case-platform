import uuid

from fastapi import APIRouter
from pydantic import BaseModel as PydanticBaseModel

from app.core.dependencies import AsyncSessionDep
from app.modules.notification.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationCreate(PydanticBaseModel):
    title: str
    content: str | None = None
    type: str = "info"
    ref_type: str | None = None
    ref_id: uuid.UUID | None = None
    user_id: uuid.UUID


@router.get("/")
async def list_notifications(
    session: AsyncSessionDep,
    user_id: uuid.UUID | None = None,
    unread_only: bool = False,
) -> list[dict]:
    svc = NotificationService(session)
    notifications = await svc.list_notifications(user_id, unread_only)
    return [
        {
            "id": str(n.id),
            "title": n.title,
            "content": n.content,
            "type": n.type,
            "is_read": n.is_read,
            "ref_type": n.ref_type,
            "ref_id": str(n.ref_id) if n.ref_id else None,
            "created_at": n.created_at.isoformat() if n.created_at else "",
        }
        for n in notifications
    ]


@router.post("/", status_code=201)
async def create_notification(data: NotificationCreate, session: AsyncSessionDep) -> dict:
    svc = NotificationService(session)
    n = await svc.create_notification(
        title=data.title,
        content=data.content,
        type=data.type,
        ref_type=data.ref_type,
        ref_id=data.ref_id,
        user_id=data.user_id,
    )
    return {"id": str(n.id)}


@router.post("/{notification_id}/read")
async def mark_read(notification_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = NotificationService(session)
    success = await svc.mark_read(notification_id)
    return {"ok": success}


@router.post("/mark-all-read/{user_id}")
async def mark_all_read(user_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = NotificationService(session)
    count = await svc.mark_all_read(user_id)
    return {"marked_read": count}
