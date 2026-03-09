import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.dependencies import AsyncSessionDep
from app.modules.test_plan.schemas import (
    TestPlanCreate,
    TestPlanResponse,
    TestPlanStatsResponse,
    TestPlanUpdate,
)
from app.modules.test_plan.service import TestPlanService

router = APIRouter(prefix="/test-plans", tags=["test-plans"])


@router.get("", response_model=list[TestPlanResponse])
async def list_plans(
    session: AsyncSessionDep,
    iteration_id: Annotated[uuid.UUID | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> list[TestPlanResponse]:
    svc = TestPlanService(session)
    plans = await svc.list_plans(iteration_id, status_filter)
    return [TestPlanResponse.model_validate(p) for p in plans]


@router.get("/stats", response_model=TestPlanStatsResponse)
async def get_stats(
    session: AsyncSessionDep,
    iteration_id: Annotated[uuid.UUID, Query()],
) -> TestPlanStatsResponse:
    svc = TestPlanService(session)
    return await svc.get_stats(iteration_id)


@router.get("/{plan_id}", response_model=TestPlanResponse)
async def get_plan(plan_id: uuid.UUID, session: AsyncSessionDep) -> TestPlanResponse:
    svc = TestPlanService(session)
    plan = await svc.get_plan(plan_id)
    return TestPlanResponse.model_validate(plan)


@router.post("", response_model=TestPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(data: TestPlanCreate, session: AsyncSessionDep) -> TestPlanResponse:
    svc = TestPlanService(session)
    plan = await svc.create_plan(data)
    return TestPlanResponse.model_validate(plan)


@router.patch("/{plan_id}", response_model=TestPlanResponse)
async def update_plan(plan_id: uuid.UUID, data: TestPlanUpdate, session: AsyncSessionDep) -> TestPlanResponse:
    svc = TestPlanService(session)
    plan = await svc.update_plan(plan_id, data)
    return TestPlanResponse.model_validate(plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: uuid.UUID, session: AsyncSessionDep) -> None:
    svc = TestPlanService(session)
    await svc.soft_delete(plan_id)
