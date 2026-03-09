import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel as PydanticBaseModel

from app.core.dependencies import AsyncSessionDep
from app.modules.test_plan.service import TestPlanService

router = APIRouter(prefix="/test-plans", tags=["test-plans"])


class TestPlanCreate(PydanticBaseModel):
    iteration_id: uuid.UUID
    name: str
    description: str | None = None
    scope: dict | None = None


class TestPlanStatusUpdate(PydanticBaseModel):
    status: str


@router.get("/")
async def list_plans(session: AsyncSessionDep, iteration_id: uuid.UUID | None = None) -> list[dict]:
    svc = TestPlanService(session)
    plans = await svc.list_plans(iteration_id)
    return [
        {
            "id": str(p.id),
            "iteration_id": str(p.iteration_id),
            "name": p.name,
            "status": p.status,
            "test_case_count": p.test_case_count,
            "created_at": p.created_at.isoformat() if p.created_at else "",
        }
        for p in plans
    ]


@router.get("/{plan_id}")
async def get_plan(plan_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = TestPlanService(session)
    plan = await svc.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Test plan not found")
    return {
        "id": str(plan.id),
        "iteration_id": str(plan.iteration_id),
        "name": plan.name,
        "description": plan.description,
        "status": plan.status,
        "scope": plan.scope,
        "test_case_count": plan.test_case_count,
    }


@router.post("/", status_code=201)
async def create_plan(data: TestPlanCreate, session: AsyncSessionDep) -> dict:
    svc = TestPlanService(session)
    plan = await svc.create_plan(
        iteration_id=data.iteration_id,
        name=data.name,
        description=data.description,
        scope=data.scope,
    )
    return {"id": str(plan.id), "name": plan.name}


@router.patch("/{plan_id}/status")
async def update_status(plan_id: uuid.UUID, data: TestPlanStatusUpdate, session: AsyncSessionDep) -> dict:
    svc = TestPlanService(session)
    plan = await svc.update_status(plan_id, data.status)
    if not plan:
        raise HTTPException(status_code=404, detail="Test plan not found")
    return {"id": str(plan.id), "status": plan.status}


@router.delete("/{plan_id}")
async def delete_plan(plan_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = TestPlanService(session)
    success = await svc.soft_delete(plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test plan not found")
    return {"ok": True}
