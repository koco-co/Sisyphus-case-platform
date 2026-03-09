"""M02 历史数据导入清洗 — Pydantic Schemas"""

from __future__ import annotations

import uuid

from pydantic import Field

from app.shared.base_schema import BaseResponse, BaseSchema

# ── Request ────────────────────────────────────────────────────────


class ImportJobCreate(BaseSchema):
    file_type: str = Field(..., pattern="^(csv|excel|markdown)$")
    product_id: uuid.UUID | None = None


class ImportRecordAction(BaseSchema):
    """用户对导入记录的操作。"""

    action: str = Field(..., pattern="^(import|skip|merge)$")
    merge_target_id: uuid.UUID | None = None


class BatchRecordAction(BaseSchema):
    """批量操作请求。"""

    record_ids: list[uuid.UUID]
    action: str = Field(..., pattern="^(import|skip)$")


class FieldMappingUpdate(BaseSchema):
    """手动调整字段映射。"""

    mapping: dict[str, str | None]


# ── Response ───────────────────────────────────────────────────────


class ImportJobResponse(BaseResponse):
    file_name: str
    file_type: str
    status: str
    total_records: int
    success_count: int
    failed_count: int
    duplicate_count: int
    product_id: uuid.UUID | None
    error_message: str | None
    health_report: dict | None
    field_mapping: dict | None = None


class ImportRecordResponse(BaseResponse):
    job_id: uuid.UUID
    row_number: int
    original_title: str | None = None
    mapped_title: str | None = None
    raw_data: dict
    mapped_data: dict | None
    status: str
    match_score: float | None = None
    error_message: str | None
    duplicate_of: uuid.UUID | None


class FieldMappingResponse(BaseSchema):
    """字段映射结果。"""

    mapping: dict[str, str | None]
    unmapped_columns: list[str]


class HealthReportResponse(BaseSchema):
    """导入健康报告。"""

    job_id: uuid.UUID
    total_records: int
    valid_count: int
    error_count: int
    duplicate_count: int
    field_coverage: dict[str, float]
    issues: list[dict]
    summary: str


class TaskStatusResponse(BaseSchema):
    """Celery 任务状态。"""

    task_id: str
    status: str
    progress: int | None = None
    step: str | None = None
    result: dict | None = None
