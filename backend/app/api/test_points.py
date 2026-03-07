from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain.test_points.service import generate_test_point_version
from app.schemas.test_point import TestPointVersionResponse

router = APIRouter(tags=['test-points'])


@router.post('/api/tasks/{task_id}/test-point-versions:generate', response_model=TestPointVersionResponse, status_code=202)
async def create_test_point_version(task_id: int, db: AsyncSession = Depends(get_db)):
    version = await generate_test_point_version(db, task_id)
    if version is None:
        raise HTTPException(status_code=404, detail='结构化版本不存在')
    return version
