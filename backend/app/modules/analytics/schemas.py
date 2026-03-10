import uuid
from datetime import date

from app.shared.base_schema import BaseResponse, BaseSchema


class SnapshotResponse(BaseResponse):
    iteration_id: uuid.UUID
    snapshot_date: date
    metrics: dict
    trends: dict | None


class DashboardResponse(BaseSchema):
    overview: dict
    priority_distribution: list[dict]
    status_distribution: list[dict]
    source_distribution: list[dict]
    execution_summary: dict


class TrendDataResponse(BaseSchema):
    dates: list[str]
    metrics: dict[str, list]


class FrontendTrendResponse(BaseSchema):
    case_count_trend: list[dict]
    pass_rate_trend: list[dict]


class QualityScoreResponse(BaseSchema):
    iteration_id: uuid.UUID
    score: float
    breakdown: dict
    grade: str
