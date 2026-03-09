import uuid as _uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.testcases.models import TestCase, TestCaseVersion
from app.modules.testcases.schemas import TestCaseCreate, TestCaseUpdate


class TestCaseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── List (paginated + filtered) ────────────────────────────────

    async def list_cases(
        self,
        *,
        requirement_id: UUID | None = None,
        scene_node_id: UUID | None = None,
        status_filter: str | None = None,
        priority: str | None = None,
        case_type: str | None = None,
        source: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TestCase], int]:
        q = select(TestCase).where(TestCase.deleted_at.is_(None))
        count_q = select(func.count(TestCase.id)).select_from(TestCase).where(TestCase.deleted_at.is_(None))

        for col, val in (
            (TestCase.requirement_id, requirement_id),
            (TestCase.scene_node_id, scene_node_id),
            (TestCase.status, status_filter),
            (TestCase.priority, priority),
            (TestCase.case_type, case_type),
            (TestCase.source, source),
        ):
            if val is not None:
                q = q.where(col == val)
                count_q = count_q.where(col == val)

        if keyword:
            q = q.where(TestCase.title.ilike(f"%{keyword}%"))
            count_q = count_q.where(TestCase.title.ilike(f"%{keyword}%"))

        total = (await self.session.execute(count_q)).scalar() or 0
        q = q.order_by(TestCase.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    # ── Single read ────────────────────────────────────────────────

    async def get_case(self, case_id: UUID) -> TestCase:
        q = select(TestCase).where(TestCase.id == case_id, TestCase.deleted_at.is_(None))
        result = await self.session.execute(q)
        tc = result.scalar_one_or_none()
        if not tc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test case not found",
            )
        return tc

    # ── Idempotent create ──────────────────────────────────────────

    async def create_case(self, data: TestCaseCreate) -> TestCase:
        case_id_str = data.case_id or f"TC-{_uuid.uuid4().hex[:8].upper()}"

        # Idempotent: if caller-supplied case_id exists, return it
        if data.case_id:
            q = select(TestCase).where(
                TestCase.case_id == case_id_str,
                TestCase.deleted_at.is_(None),
            )
            existing = (await self.session.execute(q)).scalar_one_or_none()
            if existing:
                return existing

        payload = data.model_dump(exclude={"case_id"})
        tc = TestCase(**payload, case_id=case_id_str)
        self.session.add(tc)
        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    # ── Update (with version snapshot) ─────────────────────────────

    async def update_case(self, case_id: UUID, data: TestCaseUpdate) -> TestCase:
        tc = await self.get_case(case_id)

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return tc

        await self._create_version(tc)
        for key, value in updates.items():
            setattr(tc, key, value)
        tc.version += 1

        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    # ── Soft delete ────────────────────────────────────────────────

    async def soft_delete_case(self, case_id: UUID) -> None:
        tc = await self.get_case(case_id)
        tc.deleted_at = datetime.now(UTC)
        await self.session.commit()

    # ── Batch status update ────────────────────────────────────────

    async def batch_update_status(self, case_ids: list[UUID], new_status: str) -> int:
        count = 0
        for cid in case_ids:
            q = select(TestCase).where(TestCase.id == cid, TestCase.deleted_at.is_(None))
            tc = (await self.session.execute(q)).scalar_one_or_none()
            if tc:
                tc.status = new_status
                count += 1
        await self.session.commit()
        return count

    # ── Convenience queries ────────────────────────────────────────

    async def get_cases_by_requirement(self, requirement_id: UUID) -> list[TestCase]:
        q = (
            select(TestCase)
            .where(
                TestCase.requirement_id == requirement_id,
                TestCase.deleted_at.is_(None),
            )
            .order_by(TestCase.created_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_cases_by_scene_node(self, node_id: UUID) -> list[TestCase]:
        q = (
            select(TestCase)
            .where(
                TestCase.scene_node_id == node_id,
                TestCase.deleted_at.is_(None),
            )
            .order_by(TestCase.created_at.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def count_by_status(self, requirement_id: UUID | None = None) -> tuple[int, list[dict[str, object]]]:
        q = (
            select(TestCase.status, func.count(TestCase.id))
            .where(TestCase.deleted_at.is_(None))
            .group_by(TestCase.status)
        )
        if requirement_id:
            q = q.where(TestCase.requirement_id == requirement_id)

        result = await self.session.execute(q)
        rows = result.all()
        total = sum(row[1] for row in rows)
        by_status = [{"status": row[0], "count": row[1]} for row in rows]
        return total, by_status

    # ── Version management (B-M06-05) ─────────────────────────────

    async def list_versions(self, case_id: UUID) -> list[TestCaseVersion]:
        q = (
            select(TestCaseVersion)
            .where(TestCaseVersion.test_case_id == case_id)
            .order_by(TestCaseVersion.version.desc())
        )
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_version(self, case_id: UUID, version: int) -> TestCaseVersion:
        q = select(TestCaseVersion).where(
            TestCaseVersion.test_case_id == case_id,
            TestCaseVersion.version == version,
        )
        result = await self.session.execute(q)
        ver = result.scalar_one_or_none()
        if not ver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version} not found",
            )
        return ver

    # ── Review workflow (B-M06-06) ─────────────────────────────────

    async def submit_for_review(self, case_id: UUID) -> TestCase:
        tc = await self.get_case(case_id)
        if tc.status not in ("draft", "rejected"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit for review from status '{tc.status}'",
            )
        await self._create_version(tc, change_reason="Submitted for review")
        tc.status = "review"
        tc.version += 1
        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    async def approve_case(self, case_id: UUID, reviewer_id: UUID) -> TestCase:
        tc = await self.get_case(case_id)
        if tc.status != "review":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only cases in 'review' status can be approved",
            )
        await self._create_version(tc, change_reason=f"Approved by {reviewer_id}")
        tc.status = "approved"
        tc.reviewer_id = reviewer_id
        tc.review_comment = None
        tc.version += 1
        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    async def reject_case(self, case_id: UUID, reviewer_id: UUID, reason: str | None = None) -> TestCase:
        tc = await self.get_case(case_id)
        if tc.status != "review":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only cases in 'review' status can be rejected",
            )
        await self._create_version(tc, change_reason=f"Rejected: {reason or 'No reason given'}")
        tc.status = "rejected"
        tc.reviewer_id = reviewer_id
        tc.review_comment = reason
        tc.version += 1
        await self.session.commit()
        await self.session.refresh(tc)
        return tc

    # ── Full traceability (B-M06-07) ──────────────────────────────

    async def get_traceability(self, case_id: UUID) -> dict:
        """Return full traceability chain: TestCase → TestPoint → SceneMap → Requirement → Iteration → Product."""
        from app.modules.products.models import Iteration, Product, Requirement
        from app.modules.scene_map.models import SceneMap, TestPoint

        tc = await self.get_case(case_id)

        result: dict[str, object] = {"test_case": tc}

        # TestPoint (via scene_node_id)
        test_point = None
        scene_map = None
        if tc.scene_node_id:
            tp_q = select(TestPoint).where(
                TestPoint.id == tc.scene_node_id,
                TestPoint.deleted_at.is_(None),
            )
            test_point = (await self.session.execute(tp_q)).scalar_one_or_none()

        if test_point:
            result["test_point"] = test_point
            sm_q = select(SceneMap).where(
                SceneMap.id == test_point.scene_map_id,
                SceneMap.deleted_at.is_(None),
            )
            scene_map = (await self.session.execute(sm_q)).scalar_one_or_none()

        result["scene_map"] = scene_map

        # Requirement
        req = await self.session.get(Requirement, tc.requirement_id)
        result["requirement"] = req if req and req.deleted_at is None else None

        # Iteration → Product
        if req and req.deleted_at is None:
            iteration = await self.session.get(Iteration, req.iteration_id)
            result["iteration"] = iteration if iteration and iteration.deleted_at is None else None

            if iteration and iteration.deleted_at is None:
                product = await self.session.get(Product, iteration.product_id)
                result["product"] = product if product and product.deleted_at is None else None
            else:
                result["product"] = None
        else:
            result["iteration"] = None
            result["product"] = None

        return result

    # ── Internal helpers ───────────────────────────────────────────

    async def _create_version(self, tc: TestCase, *, change_reason: str | None = None) -> TestCaseVersion:
        snapshot = {
            "title": tc.title,
            "module_path": tc.module_path,
            "priority": tc.priority,
            "case_type": tc.case_type,
            "precondition": tc.precondition,
            "steps": tc.steps or [],
            "tags": tc.tags or [],
            "status": tc.status,
        }
        version = TestCaseVersion(
            test_case_id=tc.id,
            version=tc.version,
            snapshot=snapshot,
            change_reason=change_reason,
        )
        self.session.add(version)
        return version
