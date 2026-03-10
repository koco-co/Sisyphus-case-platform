from fastapi import APIRouter

from app.core.dependencies import AsyncSessionDep
from app.modules.dashboard.schemas import DashboardActivityItem, DashboardPendingItem, DashboardStatsResponse
from app.modules.dashboard.service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(session: AsyncSessionDep) -> DashboardStatsResponse:
    svc = DashboardService(session)
    return await svc.get_stats()


@router.get("/activities", response_model=list[DashboardActivityItem])
async def get_recent_activities(session: AsyncSessionDep, limit: int = 10) -> list[DashboardActivityItem]:
    svc = DashboardService(session)
    return await svc.get_recent_activities(limit)


@router.get("/pending-items", response_model=list[DashboardPendingItem])
async def get_pending_items(session: AsyncSessionDep, limit: int = 10) -> list[DashboardPendingItem]:
    svc = DashboardService(session)
    return await svc.get_pending_items(limit)


@router.get("/products-overview")
async def get_products_overview(session: AsyncSessionDep) -> list[dict]:
    svc = DashboardService(session)
    return await svc.get_products_overview()
