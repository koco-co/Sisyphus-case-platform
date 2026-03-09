import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel as PydanticBaseModel

from app.core.dependencies import AsyncSessionDep
from app.modules.recycle.service import RecycleService

router = APIRouter(prefix="/recycle", tags=["recycle"])


class RestoreRequest(PydanticBaseModel):
    entity_type: str
    item_id: uuid.UUID


@router.get("/")
async def list_deleted(session: AsyncSessionDep, entity_type: str | None = None) -> list[dict]:
    svc = RecycleService(session)
    return await svc.list_deleted_items(entity_type)


@router.post("/restore")
async def restore_item(data: RestoreRequest, session: AsyncSessionDep) -> dict:
    svc = RecycleService(session)
    success = await svc.restore_item(data.entity_type, data.item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found or not deleted")
    return {"ok": True}


@router.post("/permanent-delete")
async def permanent_delete(data: RestoreRequest, session: AsyncSessionDep) -> dict:
    svc = RecycleService(session)
    success = await svc.permanent_delete(data.entity_type, data.item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found or not deleted")
    return {"ok": True}
