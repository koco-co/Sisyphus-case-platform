from fastapi import APIRouter

from app.core.dependencies import AsyncSessionDep
from app.modules.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def get_quality_overview(session: AsyncSessionDep) -> dict:
    svc = AnalyticsService(session)
    return await svc.get_quality_overview()


@router.get("/priority-distribution")
async def get_priority_distribution(session: AsyncSessionDep) -> list[dict]:
    svc = AnalyticsService(session)
    return await svc.get_priority_distribution()


@router.get("/status-distribution")
async def get_status_distribution(session: AsyncSessionDep) -> list[dict]:
    svc = AnalyticsService(session)
    return await svc.get_status_distribution()


@router.get("/source-distribution")
async def get_source_distribution(session: AsyncSessionDep) -> list[dict]:
    svc = AnalyticsService(session)
    return await svc.get_source_distribution()
