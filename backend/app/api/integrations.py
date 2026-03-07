from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain.integrations.service import sync_task
from app.models.integration_sync_record import IntegrationSyncRecord

router = APIRouter(tags=['integrations'])


class SyncRequest(BaseModel):
    provider: str


@router.post('/api/tasks/{task_id}:sync', status_code=202)
async def trigger_sync(task_id: int, payload: SyncRequest, db: AsyncSession = Depends(get_db)):
    record = await sync_task(db, task_id, payload.provider)
    if record is None:
        raise HTTPException(status_code=404, detail='任务不存在')
    return {
        'task_id': task_id,
        'provider': record.provider,
        'status': record.status,
        'output_path': record.output_path,
    }


@router.get('/api/tasks/{task_id}/sync-records')
async def get_sync_records(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(IntegrationSyncRecord).where(IntegrationSyncRecord.task_id == task_id).order_by(IntegrationSyncRecord.id.desc())
    )
    records = result.scalars().all()
    return [
        {
            'id': record.id,
            'provider': record.provider,
            'status': record.status,
            'output_path': record.output_path,
        }
        for record in records
    ]
