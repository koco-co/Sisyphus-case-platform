import uuid

from app.shared.base_schema import BaseResponse, BaseSchema


class DiagnosisRiskResponse(BaseResponse):
    report_id: uuid.UUID
    level: str
    title: str
    description: str | None
    risk_status: str


class DiagnosisRiskUpdate(BaseSchema):
    risk_status: str


class DiagnosisReportResponse(BaseResponse):
    requirement_id: uuid.UUID
    status: str
    overall_score: float | None
    summary: str | None
    risk_count_high: int
    risk_count_medium: int
    risk_count_industry: int
    risks: list[DiagnosisRiskResponse] = []


class ChatRequest(BaseSchema):
    message: str
