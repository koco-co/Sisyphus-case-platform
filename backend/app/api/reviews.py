from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain.reviews.service import build_coverage_report, publish_task

router = APIRouter(tags=['reviews'])


@router.get('/api/tasks/{task_id}/coverage-report')
async def get_coverage_report(task_id: int, db: AsyncSession = Depends(get_db)):
    report = await build_coverage_report(db, task_id)
    if report is None:
        raise HTTPException(status_code=404, detail='任务不存在')
    return report


@router.get('/api/tasks/{task_id}/quality-report')
async def get_quality_report(task_id: int, db: AsyncSession = Depends(get_db)):
    report = await build_coverage_report(db, task_id)
    if report is None:
        raise HTTPException(status_code=404, detail='任务不存在')
    return {
        **report,
        'quality_score': 0.9 if report['generated_cases'] else 0.0,
    }


@router.post('/api/tasks/{task_id}:publish')
async def publish(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await publish_task(db, task_id)
    if result is None:
        raise HTTPException(status_code=404, detail='任务不存在')
    if result.get('error') == 'approved_case_package_missing':
        raise HTTPException(status_code=400, detail='缺少已审核通过的用例包')
    return result
