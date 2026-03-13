import uuid
from typing import Literal

from pydantic import Field

from app.shared.base_schema import BaseResponse, BaseSchema
from app.shared.pagination import PaginatedResponse

# ── Step schema ────────────────────────────────────────────────────


class TestCaseStepSchema(BaseSchema):
    step: int
    action: str
    expected: str


# ── Create / Update ────────────────────────────────────────────────

CaseTypeLiteral = Literal[
    "functional",
    "boundary",
    "exception",
    "performance",
    "security",
    "compatibility",
]
StatusLiteral = Literal["draft", "review", "approved", "rejected", "deprecated"]
PriorityLiteral = Literal["P0", "P1", "P2", "P3"]
SourceLiteral = Literal["ai_generated", "manual", "imported"]


class TestCaseCreate(BaseSchema):
    requirement_id: uuid.UUID
    scene_node_id: uuid.UUID | None = None
    generation_session_id: uuid.UUID | None = None
    case_id: str | None = None
    title: str
    module_path: str | None = None
    precondition: str | None = None
    priority: PriorityLiteral = "P1"
    case_type: CaseTypeLiteral = "functional"
    source: SourceLiteral = "manual"
    steps: list[TestCaseStepSchema] = []
    tags: list[str] = []
    created_by: uuid.UUID | None = None


class TestCaseUpdate(BaseSchema):
    title: str | None = None
    module_path: str | None = None
    precondition: str | None = None
    priority: PriorityLiteral | None = None
    case_type: CaseTypeLiteral | None = None
    status: StatusLiteral | None = None
    steps: list[TestCaseStepSchema] | None = None
    tags: list[str] | None = None


# ── Response ───────────────────────────────────────────────────────


class TestCaseResponse(BaseResponse):
    requirement_id: uuid.UUID | None
    scene_node_id: uuid.UUID | None
    generation_session_id: uuid.UUID | None
    case_id: str
    title: str
    module_path: str | None
    precondition: str | None
    priority: str
    case_type: str
    status: str
    source: str
    steps: list[TestCaseStepSchema]
    tags: list[str]
    ai_score: float | None
    clean_status: str | None = None
    quality_score: float | None = None
    original_raw: dict | None = None
    created_by: uuid.UUID | None
    reviewer_id: uuid.UUID | None = None
    review_comment: str | None = None
    version: int


TestCaseListResponse = PaginatedResponse[TestCaseResponse]


# ── Filter / Batch ─────────────────────────────────────────────────


class TestCaseFilter(BaseSchema):
    requirement_id: uuid.UUID | None = None
    scene_node_id: uuid.UUID | None = None
    priority: str | None = None
    case_type: str | None = None
    status: str | None = None
    source: str | None = None
    keyword: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class TestCaseBatchAction(BaseSchema):
    case_ids: list[uuid.UUID]
    status: StatusLiteral


# ── Stats ──────────────────────────────────────────────────────────


class StatusCountItem(BaseSchema):
    status: str
    count: int


class TestCaseStatsResponse(BaseSchema):
    total: int
    by_status: list[StatusCountItem]


# ── Version ────────────────────────────────────────────────────────


class TestCaseVersionResponse(BaseResponse):
    test_case_id: uuid.UUID
    version: int
    snapshot: dict
    change_reason: str | None


# ── Review ─────────────────────────────────────────────────────────


class ReviewRequest(BaseSchema):
    reviewer_id: uuid.UUID | None = None
    reason: str | None = None


# ── Traceability ───────────────────────────────────────────────────


class TraceabilityResponse(BaseSchema):
    test_case: TestCaseResponse
    test_point: dict | None = None
    scene_map: dict | None = None
    requirement: dict | None = None
    iteration: dict | None = None
    product: dict | None = None


# ── Folder schemas ─────────────────────────────────────────────────


class FolderCreate(BaseSchema):
    name: str = Field(..., max_length=200)
    parent_id: uuid.UUID | None = None


class FolderUpdate(BaseSchema):
    name: str | None = None
    sort_order: int | None = None


class FolderResponse(BaseResponse):
    name: str
    parent_id: uuid.UUID | None
    sort_order: int
    level: int
    is_system: bool = False
    case_count: int = 0


class FolderTreeNode(BaseSchema):
    id: uuid.UUID
    name: str
    level: int
    sort_order: int
    is_system: bool = False
    case_count: int = 0
    children: list["FolderTreeNode"] = []


class MoveCasesRequest(BaseSchema):
    case_ids: list[uuid.UUID]
    folder_id: uuid.UUID | None = None


class FolderReorderItem(BaseSchema):
    id: uuid.UUID
    sort_order: int


class FolderReorderRequest(BaseSchema):
    items: list[FolderReorderItem]
