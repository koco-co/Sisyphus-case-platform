import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.dependencies import AsyncSessionDep
from app.modules.collaboration.schemas import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    ReviewCreate,
    ReviewDecisionResponse,
    ReviewDecisionSubmit,
    ReviewResponse,
    ReviewStatusResponse,
    SharedReviewResponse,
    ShareTokenResponse,
)
from app.modules.collaboration.service import CollaborationService
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


@router.post("/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(data: CommentCreate, session: AsyncSessionDep) -> CommentResponse:
    svc = CollaborationService(session)
    comment = await svc.create_comment(data)
    return CommentResponse.model_validate(comment)


@router.get("/comments", response_model=PaginatedResponse[CommentResponse])
async def list_comments(
    session: AsyncSessionDep,
    entity_type: Annotated[str, Query(description="实体类型")],
    entity_id: Annotated[uuid.UUID, Query(description="实体 ID")],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> dict:
    svc = CollaborationService(session)
    comments, total = await svc.get_comments_by_entity(entity_type, entity_id, page, page_size)
    return {
        "items": [CommentResponse.model_validate(c) for c in comments],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.patch("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(comment_id: uuid.UUID, data: CommentUpdate, session: AsyncSessionDep) -> CommentResponse:
    svc = CollaborationService(session)
    comment = await svc.update_comment(comment_id, data)
    return CommentResponse.model_validate(comment)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: uuid.UUID, session: AsyncSessionDep) -> None:
    svc = CollaborationService(session)
    await svc.delete_comment(comment_id)


# ── Review Flow (B-M18-04) ───────────────────────────────────────


@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(data: ReviewCreate, session: AsyncSessionDep) -> ReviewResponse:
    svc = CollaborationService(session)
    review = await svc.create_review(data)
    return ReviewResponse.model_validate(review)


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: uuid.UUID, session: AsyncSessionDep) -> ReviewResponse:
    svc = CollaborationService(session)
    review = await svc.get_review(review_id)
    if not review:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse.model_validate(review)


@router.get("/reviews/{review_id}/status", response_model=ReviewStatusResponse)
async def get_review_status(review_id: uuid.UUID, session: AsyncSessionDep) -> ReviewStatusResponse:
    svc = CollaborationService(session)
    result = await svc.get_review_status(review_id)
    decisions = result.pop("decisions", [])
    return ReviewStatusResponse(
        **result,
        decisions=[ReviewDecisionResponse.model_validate(d) for d in decisions],
    )


@router.post(
    "/reviews/{review_id}/decisions",
    response_model=ReviewDecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_decision(
    review_id: uuid.UUID, data: ReviewDecisionSubmit, session: AsyncSessionDep
) -> ReviewDecisionResponse:
    svc = CollaborationService(session)
    decision = await svc.submit_decision(review_id, data)
    return ReviewDecisionResponse.model_validate(decision)


@router.get("/reviews", response_model=list[ReviewResponse])
async def list_reviews(
    session: AsyncSessionDep,
    entity_type: Annotated[str, Query(description="实体类型")],
    entity_id: Annotated[uuid.UUID, Query(description="实体 ID")],
) -> list[ReviewResponse]:
    svc = CollaborationService(session)
    reviews = await svc.list_reviews_by_entity(entity_type, entity_id)
    return [ReviewResponse.model_validate(r) for r in reviews]


# ── Review Share Token (B-M18-05) ────────────────────────────────


@router.post(
    "/reviews/{review_id}/share",
    response_model=ShareTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_share_link(
    review_id: uuid.UUID,
    created_by: Annotated[uuid.UUID, Query(description="创建分享链接的用户 ID")],
    session: AsyncSessionDep,
) -> ShareTokenResponse:
    svc = CollaborationService(session)
    share = await svc.generate_share_token(review_id, created_by)
    return ShareTokenResponse(
        token=share.token,
        review_id=share.review_id,
        share_url=f"/api/collaboration/shared/{share.token}",
    )


@router.get("/shared/{token}", response_model=SharedReviewResponse)
async def get_shared_review(token: str, session: AsyncSessionDep) -> SharedReviewResponse:
    svc = CollaborationService(session)
    result = await svc.get_review_by_token(token)
    return SharedReviewResponse(
        review=ReviewResponse.model_validate(result["review"]),
        decisions=[ReviewDecisionResponse.model_validate(d) for d in result["decisions"]],
        entity_snapshot=result.get("entity_snapshot"),
    )


@router.delete("/shared/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_token(token: str, session: AsyncSessionDep) -> None:
    svc = CollaborationService(session)
    await svc.revoke_share_token(token)
