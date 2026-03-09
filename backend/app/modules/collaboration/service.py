import secrets
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.collaboration.models import (
    CollaborationComment,
    Review,
    ReviewDecision,
    ReviewShareToken,
)
from app.modules.collaboration.schemas import CommentCreate, CommentUpdate, ReviewCreate, ReviewDecisionSubmit


class CollaborationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_comment(self, data: CommentCreate) -> CollaborationComment:
        comment = CollaborationComment(**data.model_dump())
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def get_comments_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[CollaborationComment], int]:
        base_where = [
            CollaborationComment.entity_type == entity_type,
            CollaborationComment.entity_id == entity_id,
            CollaborationComment.deleted_at.is_(None),
        ]
        count_q = select(func.count()).select_from(CollaborationComment).where(*base_where)
        total = (await self.session.execute(count_q)).scalar() or 0

        q = (
            select(CollaborationComment)
            .where(*base_where)
            .order_by(CollaborationComment.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def update_comment(self, comment_id: UUID, data: CommentUpdate) -> CollaborationComment:
        comment = await self.session.get(CollaborationComment, comment_id)
        if not comment or comment.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        comment.content = data.content
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: UUID) -> None:
        comment = await self.session.get(CollaborationComment, comment_id)
        if not comment or comment.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        comment.deleted_at = datetime.now(UTC)
        await self.session.commit()

    # ── Review Flow (B-M18-04) ───────────────────────────────────────

    async def create_review(self, data: ReviewCreate) -> Review:
        """创建测试点多人评审。"""
        review = Review(
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            title=data.title,
            description=data.description,
            created_by=data.created_by,
            status="pending",
            reviewer_ids=[str(uid) for uid in data.reviewer_ids],
        )
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def submit_decision(self, review_id: UUID, data: ReviewDecisionSubmit) -> ReviewDecision:
        """提交评审决定（approve / reject / request_changes）。"""
        review = await self._get_review_or_raise(review_id)

        # 检查评审人是否在列表中
        reviewer_ids = review.reviewer_ids or []
        if str(data.reviewer_id) not in reviewer_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Reviewer not in review list",
            )

        # 幂等：检查是否已提交
        existing_q = select(ReviewDecision).where(
            ReviewDecision.review_id == review_id,
            ReviewDecision.reviewer_id == data.reviewer_id,
            ReviewDecision.deleted_at.is_(None),
        )
        existing = (await self.session.execute(existing_q)).scalar_one_or_none()

        if existing:
            existing.decision = data.decision
            existing.comment = data.comment
            await self.session.commit()
            await self.session.refresh(existing)
            await self._update_review_status(review)
            return existing

        decision = ReviewDecision(
            review_id=review_id,
            reviewer_id=data.reviewer_id,
            decision=data.decision,
            comment=data.comment,
        )
        self.session.add(decision)
        await self.session.commit()
        await self.session.refresh(decision)
        await self._update_review_status(review)
        return decision

    async def get_review_status(self, review_id: UUID) -> dict:
        """获取评审状态摘要。"""
        review = await self._get_review_or_raise(review_id)
        decisions = await self._get_decisions(review_id)

        reviewer_ids = review.reviewer_ids or []
        approved = sum(1 for d in decisions if d.decision == "approved")
        rejected = sum(1 for d in decisions if d.decision == "rejected")
        pending = len(reviewer_ids) - len(decisions)

        return {
            "review_id": review_id,
            "status": review.status,
            "total_reviewers": len(reviewer_ids),
            "approved_count": approved,
            "rejected_count": rejected,
            "pending_count": max(pending, 0),
            "decisions": decisions,
        }

    async def get_review(self, review_id: UUID) -> Review | None:
        q = select(Review).where(Review.id == review_id, Review.deleted_at.is_(None))
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def list_reviews_by_entity(self, entity_type: str, entity_id: UUID) -> list[Review]:
        q = (
            select(Review)
            .where(
                Review.entity_type == entity_type,
                Review.entity_id == entity_id,
                Review.deleted_at.is_(None),
            )
            .order_by(Review.created_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    # ── Review Share Token (B-M18-05) ────────────────────────────────

    async def generate_share_token(self, review_id: UUID, created_by: UUID) -> ReviewShareToken:
        """生成唯一 token 分享链接。"""
        await self._get_review_or_raise(review_id)

        token = secrets.token_urlsafe(32)
        share = ReviewShareToken(
            review_id=review_id,
            token=token,
            created_by=created_by,
            is_active=True,
        )
        self.session.add(share)
        await self.session.commit()
        await self.session.refresh(share)
        return share

    async def get_review_by_token(self, token: str) -> dict:
        """基于 token 获取只读评审信息。"""
        q = select(ReviewShareToken).where(
            ReviewShareToken.token == token,
            ReviewShareToken.is_active.is_(True),
            ReviewShareToken.deleted_at.is_(None),
        )
        share = (await self.session.execute(q)).scalar_one_or_none()
        if not share:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired share token")

        review = await self.get_review(share.review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        decisions = await self._get_decisions(share.review_id)
        return {"review": review, "decisions": decisions}

    async def revoke_share_token(self, token: str) -> None:
        """撤销分享 token。"""
        q = select(ReviewShareToken).where(
            ReviewShareToken.token == token,
            ReviewShareToken.deleted_at.is_(None),
        )
        share = (await self.session.execute(q)).scalar_one_or_none()
        if not share:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
        share.is_active = False
        await self.session.commit()

    # ── Private helpers ──────────────────────────────────────────────

    async def _get_review_or_raise(self, review_id: UUID) -> Review:
        review = await self.get_review(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        return review

    async def _get_decisions(self, review_id: UUID) -> list[ReviewDecision]:
        q = (
            select(ReviewDecision)
            .where(
                ReviewDecision.review_id == review_id,
                ReviewDecision.deleted_at.is_(None),
            )
            .order_by(ReviewDecision.created_at.asc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def _update_review_status(self, review: Review) -> None:
        """自动更新评审状态：所有人 approved → approved，有人 rejected → rejected。"""
        decisions = await self._get_decisions(review.id)
        reviewer_ids = review.reviewer_ids or []

        if not reviewer_ids:
            return

        if len(decisions) < len(reviewer_ids):
            review.status = "in_progress"
        elif all(d.decision == "approved" for d in decisions):
            review.status = "approved"
        elif any(d.decision == "rejected" for d in decisions):
            review.status = "rejected"
        else:
            review.status = "completed"

        await self.session.commit()
