import uuid
from datetime import datetime

from app.shared.base_schema import BaseResponse, BaseSchema


class ExecutionResultCreate(BaseSchema):
    test_case_id: uuid.UUID
    iteration_id: uuid.UUID
    status: str
    executor_id: uuid.UUID | None = None
    actual_result: str | None = None
    defect_id: str | None = None
    environment: str | None = None
    duration_seconds: int | None = None
    evidence: dict | None = None


class ExecutionResultUpdate(BaseSchema):
    status: str | None = None
    executor_id: uuid.UUID | None = None
    actual_result: str | None = None
    defect_id: str | None = None
    environment: str | None = None
    duration_seconds: int | None = None
    evidence: dict | None = None


class ExecutionResultResponse(BaseResponse):
    test_case_id: uuid.UUID
    iteration_id: uuid.UUID
    executor_id: uuid.UUID | None = None
    status: str
    actual_result: str | None = None
    defect_id: str | None = None
    environment: str | None = None
    duration_seconds: int | None = None
    executed_at: datetime
    evidence: dict | None = None


class BatchExecutionRequest(BaseSchema):
    results: list[ExecutionResultCreate]


class ExecutionSummaryResponse(BaseSchema):
    iteration_id: uuid.UUID
    total: int
    passed: int
    failed: int
    blocked: int
    skipped: int
    pass_rate: float
    executed_at_range: dict | None = None


class MarkFailedRequest(BaseSchema):
    test_case_id: uuid.UUID
    iteration_id: uuid.UUID
    defect_id: str | None = None
    actual_result: str | None = None


# ── RAG Weight Adjustment (B-M13-04) ──────────────────────────────


class RAGWeightAdjustItem(BaseSchema):
    test_case_id: uuid.UUID
    status: str


class RAGWeightAdjustRequest(BaseSchema):
    execution_results: list[RAGWeightAdjustItem]


class RAGWeightAdjustResponse(BaseSchema):
    adjusted_count: int
    skipped_count: int
    adjustments: list[dict] = []


# ── Jira/Xray Results Sync (B-M13-06) ────────────────────────────


class JiraSyncConfig(BaseSchema):
    base_url: str
    auth_token: str
    project_key: str | None = None


class JiraSyncRequest(BaseSchema):
    case_ids: list[uuid.UUID]
    jira_config: JiraSyncConfig


class JiraSyncResponse(BaseSchema):
    status: str
    synced_count: int = 0
    failed_count: int = 0
    results: list[dict] = []
    error_message: str | None = None
