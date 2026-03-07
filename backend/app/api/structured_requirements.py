from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain.requirements.service import generate_structured_requirement_version
from app.schemas.structured_requirement import StructuredRequirementVersionResponse

router = APIRouter(tags=['structured-requirements'])


@router.post('/api/tasks/{task_id}/structured-versions:generate', response_model=StructuredRequirementVersionResponse, status_code=202)
async def create_structured_requirement_version(task_id: int, db: AsyncSession = Depends(get_db)):
    version = await generate_structured_requirement_version(db, task_id)
    if version is None:
        raise HTTPException(status_code=404, detail='任务不存在')
    return version
