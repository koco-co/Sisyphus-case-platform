import uuid

from app.shared.base_schema import BaseResponse, BaseSchema


class CommentCreate(BaseSchema):
    entity_type: str
    entity_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    parent_id: uuid.UUID | None = None


class CommentUpdate(BaseSchema):
    content: str


class CommentResponse(BaseResponse):
    entity_type: str
    entity_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    parent_id: uuid.UUID | None


# ── Review Flow (B-M18-04) ───────────────────────────────────────


class ReviewCreate(BaseSchema):
    entity_type: str
    entity_id: uuid.UUID
    title: str
    description: str | None = None
    created_by: uuid.UUID
    reviewer_ids: list[uuid.UUID]


class ReviewDecisionSubmit(BaseSchema):
    reviewer_id: uuid.UUID
    decision: str
    comment: str | None = None


class ReviewDecisionResponse(BaseResponse):
    review_id: uuid.UUID
    reviewer_id: uuid.UUID
    decision: str
    comment: str | None


class ReviewResponse(BaseResponse):
    entity_type: str
    entity_id: uuid.UUID
    title: str
    description: str | None
    created_by: uuid.UUID
    status: str
    reviewer_ids: list[uuid.UUID] = []
    decisions: list[ReviewDecisionResponse] = []


class ReviewStatusResponse(BaseSchema):
    review_id: uuid.UUID
    status: str
    total_reviewers: int
    approved_count: int
    rejected_count: int
    pending_count: int
    decisions: list[ReviewDecisionResponse] = []


# ── Review Share Token (B-M18-05) ────────────────────────────────


class ShareTokenResponse(BaseSchema):
    token: str
    review_id: uuid.UUID
    share_url: str


class SharedReviewResponse(BaseSchema):
    review: ReviewResponse
    decisions: list[ReviewDecisionResponse] = []
    entity_snapshot: dict | None = None
