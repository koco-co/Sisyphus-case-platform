from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.audit.schemas import AuditLogCreate


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_action(self, data: AuditLogCreate) -> AuditLog:
        log = AuditLog(**data.model_dump())
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_audit_logs(
        self,
        entity_type: str | None = None,
        action: str | None = None,
        user_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        q = select(AuditLog)
        count_q = select(func.count()).select_from(AuditLog)

        if entity_type:
            q = q.where(AuditLog.entity_type == entity_type)
            count_q = count_q.where(AuditLog.entity_type == entity_type)
        if action:
            q = q.where(AuditLog.action == action)
            count_q = count_q.where(AuditLog.action == action)
        if user_id:
            q = q.where(AuditLog.user_id == user_id)
            count_q = count_q.where(AuditLog.user_id == user_id)

        total = (await self.session.execute(count_q)).scalar() or 0
        q = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> list[AuditLog]:
        q = (
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.created_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())
