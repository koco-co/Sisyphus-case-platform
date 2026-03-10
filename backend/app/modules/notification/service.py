from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notification.models import Notification
from app.modules.notification.schemas import NotificationCreate


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_notification(self, data: NotificationCreate) -> Notification:
        notif = Notification(**data.model_dump())
        self.session.add(notif)
        await self.session.commit()
        await self.session.refresh(notif)
        return notif

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Notification], int]:
        q = select(Notification).where(
            Notification.user_id == user_id,
            Notification.deleted_at.is_(None),
        )
        count_q = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.deleted_at.is_(None),
            )
        )
        if unread_only:
            q = q.where(Notification.is_read.is_(False))
            count_q = count_q.where(Notification.is_read.is_(False))

        total = (await self.session.execute(count_q)).scalar() or 0
        q = q.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def mark_as_read(self, notification_id: UUID) -> bool:
        notif = await self.session.get(Notification, notification_id)
        if not notif or notif.deleted_at is not None:
            return False
        notif.is_read = True
        await self.session.commit()
        return True

    async def mark_all_as_read(self, user_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                Notification.deleted_at.is_(None),
            )
            .values(is_read=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount  # type: ignore[return-value]

    async def get_unread_count(self, user_id: UUID) -> int:
        q = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                Notification.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(q)
        return result.scalar() or 0

    async def soft_delete(self, notification_id: UUID) -> bool:
        notif = await self.session.get(Notification, notification_id)
        if not notif or notif.deleted_at is not None:
            return False
        notif.deleted_at = datetime.now(UTC)
        await self.session.commit()
        return True

    async def send_notification(
        self,
        user_id: UUID,
        title: str,
        content: str | None = None,
        notification_type: str = "system",
        related_type: str | None = None,
        related_id: UUID | None = None,
    ) -> Notification:
        """High-level helper to create and "send" a notification."""
        notif = Notification(
            user_id=user_id,
            title=title,
            content=content,
            notification_type=notification_type,
            related_type=related_type,
            related_id=related_id,
        )
        self.session.add(notif)
        await self.session.commit()
        await self.session.refresh(notif)
        return notif

    async def broadcast(
        self,
        user_ids: list[UUID],
        title: str,
        content: str | None = None,
        notification_type: str = "system",
    ) -> int:
        """Send the same notification to multiple users."""
        count = 0
        for uid in user_ids:
            notif = Notification(
                user_id=uid,
                title=title,
                content=content,
                notification_type=notification_type,
            )
            self.session.add(notif)
            count += 1
        await self.session.commit()
        return count

    async def notify_on_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        actor_id: UUID,
        target_user_ids: list[UUID],
    ) -> int:
        """Generate contextual notifications based on business events."""
        event_templates: dict[str, str] = {
            "case_generated": "测试用例已生成，请查看",
            "diagnosis_complete": "需求诊断已完成",
            "review_requested": "有新的评审请求需要处理",
            "export_ready": "导出任务已完成，可下载",
            "scene_map_updated": "场景地图已更新",
        }

        title = event_templates.get(event_type, f"系统通知: {event_type}")
        count = 0
        for uid in target_user_ids:
            if uid == actor_id:
                continue
            notif = Notification(
                user_id=uid,
                title=title,
                notification_type="event",
                related_type=entity_type,
                related_id=entity_id,
            )
            self.session.add(notif)
            count += 1
        await self.session.commit()
        return count
