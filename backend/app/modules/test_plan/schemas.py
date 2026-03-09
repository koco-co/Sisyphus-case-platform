import uuid
from datetime import date

from app.shared.base_schema import BaseResponse, BaseSchema


class TestPlanCreate(BaseSchema):
    iteration_id: uuid.UUID
    title: str
    description: str | None = None
    status: str = "draft"
    planned_cases: int = 0
    start_date: date | None = None
    end_date: date | None = None
    assigned_to: uuid.UUID | None = None
    scope: dict | None = None


class TestPlanUpdate(BaseSchema):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    planned_cases: int | None = None
    executed_cases: int | None = None
    passed_cases: int | None = None
    failed_cases: int | None = None
    blocked_cases: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    assigned_to: uuid.UUID | None = None
    scope: dict | None = None


class TestPlanResponse(BaseResponse):
    iteration_id: uuid.UUID
    title: str
    description: str | None
    status: str
    planned_cases: int
    executed_cases: int
    passed_cases: int
    failed_cases: int
    blocked_cases: int
    start_date: date | None
    end_date: date | None
    assigned_to: uuid.UUID | None
    scope: dict | None


class TestPlanStatsResponse(BaseSchema):
    total_plans: int
    draft: int
    active: int
    completed: int
    total_planned: int
    total_executed: int
    total_passed: int
    total_failed: int
    total_blocked: int
    pass_rate: float
