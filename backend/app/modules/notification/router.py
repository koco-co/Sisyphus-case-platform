import uuid

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel as PydanticBaseModel

from app.core.dependencies import AsyncSessionDep
from app.modules.notification.schemas import (
    NotificationCreate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.modules.notification.service import NotificationService
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(data: NotificationCreate, session: AsyncSessionDep) -> NotificationResponse:
    svc = NotificationService(session)
    notif = await svc.create_notification(data)
    return NotificationResponse.model_validate(notif)


@router.get("", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    session: AsyncSessionDep,
    user_id: uuid.UUID | None = None,
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> dict:
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
    svc = NotificationService(session)
    notifications, total = await svc.get_user_notifications(user_id, unread_only, page, page_size)
    return {
        "items": [NotificationResponse.model_validate(n) for n in notifications],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(user_id: uuid.UUID, session: AsyncSessionDep) -> UnreadCountResponse:
    svc = NotificationService(session)
    count = await svc.get_unread_count(user_id)
    return UnreadCountResponse(count=count)


@router.patch("/{notification_id}/read")
async def mark_as_read(notification_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = NotificationService(session)
    success = await svc.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"ok": True}


@router.patch("/read-all/{user_id}")
async def mark_all_as_read(user_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = NotificationService(session)
    count = await svc.mark_all_as_read(user_id)
    return {"marked_read": count}


class BroadcastRequest(PydanticBaseModel):
    user_ids: list[uuid.UUID]
    title: str
    content: str | None = None
    notification_type: str = "system"


class EventNotifyRequest(PydanticBaseModel):
    event_type: str
    entity_type: str
    entity_id: uuid.UUID
    actor_id: uuid.UUID
    target_user_ids: list[uuid.UUID]


@router.post("/broadcast")
async def broadcast(data: BroadcastRequest, session: AsyncSessionDep) -> dict:
    """Send the same notification to multiple users."""
    svc = NotificationService(session)
    count = await svc.broadcast(
        user_ids=data.user_ids,
        title=data.title,
        content=data.content,
        notification_type=data.notification_type,
    )
    return {"sent": count}


@router.post("/event")
async def notify_on_event(data: EventNotifyRequest, session: AsyncSessionDep) -> dict:
    """Send contextual event-based notifications."""
    svc = NotificationService(session)
    count = await svc.notify_on_event(
        event_type=data.event_type,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        actor_id=data.actor_id,
        target_user_ids=data.target_user_ids,
    )
    return {"sent": count}
