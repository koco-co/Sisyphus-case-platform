from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notification.models import Notification


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_notifications(self, user_id: UUID | None = None, unread_only: bool = False) -> list[Notification]:
        q = select(Notification).where(Notification.deleted_at.is_(None))
        if user_id:
            q = q.where(Notification.user_id == user_id)
        if unread_only:
            q = q.where(Notification.is_read.is_(False))
        q = q.order_by(Notification.created_at.desc()).limit(50)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def create_notification(self, **kwargs: object) -> Notification:
        notif = Notification(**kwargs)
        self.session.add(notif)
        await self.session.commit()
        await self.session.refresh(notif)
        return notif

    async def mark_read(self, notification_id: UUID) -> bool:
        notif = await self.session.get(Notification, notification_id)
        if not notif:
            return False
        notif.is_read = True
        await self.session.commit()
        return True

    async def mark_all_read(self, user_id: UUID) -> int:
        q = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
            Notification.deleted_at.is_(None),
        )
        result = await self.session.execute(q)
        notifications = list(result.scalars().all())
        for n in notifications:
            n.is_read = True
        await self.session.commit()
        return len(notifications)
