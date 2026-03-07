from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain.test_cases.service import generate_case_package_version
from app.schemas.test_case_package import TestCasePackageVersionResponse

router = APIRouter(tags=['case-packages'])


@router.post('/api/tasks/{task_id}/case-package-versions:generate', response_model=TestCasePackageVersionResponse, status_code=202)
async def create_case_package_version(task_id: int, db: AsyncSession = Depends(get_db)):
    version = await generate_case_package_version(db, task_id)
    if version is None:
        raise HTTPException(status_code=404, detail='测试点版本不存在')
    return version
