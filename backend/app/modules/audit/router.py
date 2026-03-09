from fastapi import APIRouter, Query

from app.core.dependencies import AsyncSessionDep
from app.modules.audit.service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
async def list_audit_logs(
    session: AsyncSessionDep,
    resource: str | None = None,
    action: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> dict:
    svc = AuditService(session)
    logs, total = await svc.list_logs(resource, action, page, page_size)
    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "resource": log.resource,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "detail": log.detail,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else "",
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
