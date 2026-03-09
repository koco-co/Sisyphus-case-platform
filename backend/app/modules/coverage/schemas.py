import uuid
from datetime import datetime

from app.shared.base_schema import BaseResponse, BaseSchema


class CoverageMatrixCreate(BaseSchema):
    requirement_id: uuid.UUID
    scene_node_id: uuid.UUID | None = None
    test_case_id: uuid.UUID | None = None
    coverage_type: str = "none"
    notes: str | None = None


class CoverageMatrixUpdate(BaseSchema):
    coverage_type: str | None = None
    notes: str | None = None


class CoverageMatrixResponse(BaseResponse):
    requirement_id: uuid.UUID
    scene_node_id: uuid.UUID | None
    test_case_id: uuid.UUID | None
    coverage_type: str
    notes: str | None


class CoverageStatsResponse(BaseSchema):
    iteration_id: uuid.UUID
    total_requirements: int
    covered_requirements: int
    partially_covered: int
    uncovered_requirements: int
    coverage_rate: float


class RequirementCoverageItem(BaseSchema):
    requirement_id: uuid.UUID
    req_id: str
    title: str
    coverage_type: str
    test_case_count: int
    scene_node_count: int


class CoverageMatrixListResponse(BaseSchema):
    items: list[RequirementCoverageItem]
    stats: CoverageStatsResponse


class UncoveredRequirementItem(BaseSchema):
    id: uuid.UUID
    req_id: str
    title: str
    status: str
    created_at: datetime
