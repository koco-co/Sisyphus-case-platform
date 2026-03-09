import uuid

from fastapi import APIRouter, Query, status

from app.core.dependencies import AsyncSessionDep
from app.modules.audit.schemas import AuditLogCreate, AuditLogResponse
from app.modules.audit.service import AuditService
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
async def create_audit_log(data: AuditLogCreate, session: AsyncSessionDep) -> AuditLogResponse:
    svc = AuditService(session)
    log = await svc.log_action(data)
    return AuditLogResponse.model_validate(log)


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    session: AsyncSessionDep,
    entity_type: str | None = None,
    action: str | None = None,
    user_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> dict:
    svc = AuditService(session)
    logs, total = await svc.get_audit_logs(entity_type, action, user_id, page, page_size)
    return {
        "items": [AuditLogResponse.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[AuditLogResponse])
async def get_entity_history(
    entity_type: str,
    entity_id: uuid.UUID,
    session: AsyncSessionDep,
) -> list[AuditLogResponse]:
    svc = AuditService(session)
    logs = await svc.get_entity_history(entity_type, entity_id)
    return [AuditLogResponse.model_validate(log) for log in logs]
