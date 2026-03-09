import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.core.dependencies import AsyncSessionDep
from app.modules.analytics.schemas import (
    DashboardResponse,
    QualityScoreResponse,
    SnapshotResponse,
    TrendDataResponse,
)
from app.modules.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

OptionalIterationId = Annotated[uuid.UUID | None, Query()]


@router.get("/overview")
async def get_quality_overview(
    session: AsyncSessionDep,
    iteration_id: OptionalIterationId = None,
) -> dict:
    svc = AnalyticsService(session)
    return await svc.get_quality_overview(iteration_id)


@router.get("/priority-distribution")
async def get_priority_distribution(
    session: AsyncSessionDep,
    iteration_id: OptionalIterationId = None,
) -> list[dict]:
    svc = AnalyticsService(session)
    return await svc.get_priority_distribution(iteration_id)


@router.get("/status-distribution")
async def get_status_distribution(
    session: AsyncSessionDep,
    iteration_id: OptionalIterationId = None,
) -> list[dict]:
    svc = AnalyticsService(session)
    return await svc.get_status_distribution(iteration_id)


@router.get("/source-distribution")
async def get_source_distribution(
    session: AsyncSessionDep,
    iteration_id: OptionalIterationId = None,
) -> list[dict]:
    svc = AnalyticsService(session)
    return await svc.get_source_distribution(iteration_id)


@router.post("/snapshot/{iteration_id}", response_model=SnapshotResponse, status_code=201)
async def take_snapshot(
    iteration_id: uuid.UUID,
    session: AsyncSessionDep,
) -> SnapshotResponse:
    svc = AnalyticsService(session)
    snapshot = await svc.take_snapshot(iteration_id)
    return SnapshotResponse.model_validate(snapshot)


@router.get("/dashboard/{iteration_id}", response_model=DashboardResponse)
async def get_dashboard_data(
    iteration_id: uuid.UUID,
    session: AsyncSessionDep,
) -> DashboardResponse:
    svc = AnalyticsService(session)
    data = await svc.get_dashboard_data(iteration_id)
    return DashboardResponse.model_validate(data)


@router.get("/trends/{iteration_id}", response_model=TrendDataResponse)
async def get_trend_data(
    iteration_id: uuid.UUID,
    session: AsyncSessionDep,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> TrendDataResponse:
    svc = AnalyticsService(session)
    data = await svc.get_trend_data(iteration_id, days)
    return TrendDataResponse.model_validate(data)


@router.get("/quality-score/{iteration_id}", response_model=QualityScoreResponse)
async def get_quality_score(
    iteration_id: uuid.UUID,
    session: AsyncSessionDep,
) -> QualityScoreResponse:
    svc = AnalyticsService(session)
    data = await svc.get_quality_score(iteration_id)
    return QualityScoreResponse.model_validate(data)


@router.get("/ai-usage")
async def get_ai_usage_stats(
    session: AsyncSessionDep,
    iteration_id: OptionalIterationId = None,
) -> dict:
    """AI call statistics: total sessions, messages, tokens, per-model breakdown."""
    svc = AnalyticsService(session)
    return await svc.get_ai_usage_stats(iteration_id)
