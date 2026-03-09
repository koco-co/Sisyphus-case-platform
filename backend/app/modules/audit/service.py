from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_action(
        self,
        user_id: UUID | None,
        action: str,
        resource: str,
        resource_id: UUID | None = None,
        detail: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            detail=detail or {},
            ip_address=ip_address,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def list_logs(
        self,
        resource: str | None = None,
        action: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        q = select(AuditLog)
        count_q = select(func.count()).select_from(AuditLog)

        if resource:
            q = q.where(AuditLog.resource == resource)
            count_q = count_q.where(AuditLog.resource == resource)
        if action:
            q = q.where(AuditLog.action == action)
            count_q = count_q.where(AuditLog.action == action)

        total = (await self.session.execute(count_q)).scalar() or 0
        q = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total
