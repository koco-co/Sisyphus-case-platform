from fastapi import APIRouter

from app.core.dependencies import AsyncSessionDep
from app.modules.dashboard.service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(session: AsyncSessionDep) -> dict:
    svc = DashboardService(session)
    return await svc.get_stats()


@router.get("/activities")
async def get_recent_activities(session: AsyncSessionDep, limit: int = 10) -> list[dict]:
    svc = DashboardService(session)
    return await svc.get_recent_activities(limit)


@router.get("/products-overview")
async def get_products_overview(session: AsyncSessionDep) -> list[dict]:
    svc = DashboardService(session)
    return await svc.get_products_overview()
