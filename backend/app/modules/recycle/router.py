from fastapi import APIRouter, Query, status

from app.core.dependencies import AsyncSessionDep
from app.modules.recycle.schemas import (
    BatchRestoreRequest,
    PermanentDeleteRequest,
    RecycleItemResponse,
    RestoreRequest,
)
from app.modules.recycle.service import RecycleService
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/recycle", tags=["recycle"])


@router.get("", response_model=PaginatedResponse[RecycleItemResponse])
async def list_deleted(
    session: AsyncSessionDep,
    type: str | None = Query(None, description="实体类型: product/iteration/requirement/testcase"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    svc = RecycleService(session)
    items, total = await svc.list_deleted(type, page, page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.post("/restore")
async def restore_item(data: RestoreRequest, session: AsyncSessionDep) -> dict:
    svc = RecycleService(session)
    await svc.restore(data.entity_type, data.entity_id)
    return {"ok": True}


@router.post("/batch-restore")
async def batch_restore(data: BatchRestoreRequest, session: AsyncSessionDep) -> dict:
    svc = RecycleService(session)
    count = await svc.batch_restore(data.items)
    return {"restored": count}


@router.delete("/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanent_delete(data: PermanentDeleteRequest, session: AsyncSessionDep) -> None:
    svc = RecycleService(session)
    await svc.permanent_delete(data.entity_type, data.entity_id)


@router.post("/cleanup")
async def cleanup_expired(
    session: AsyncSessionDep,
    retention_days: int = Query(30, ge=1, le=365, description="保留天数"),
) -> dict:
    """Permanently remove soft-deleted items older than retention_days."""
    svc = RecycleService(session)
    count = await svc.cleanup_expired(retention_days)
    return {"deleted": count, "retention_days": retention_days}
