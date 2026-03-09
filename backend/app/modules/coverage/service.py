from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.coverage.models import CoverageMatrix
from app.modules.coverage.schemas import (
    CoverageMatrixCreate,
    CoverageStatsResponse,
    RequirementCoverageItem,
    UncoveredRequirementItem,
)
from app.modules.products.models import Requirement
from app.modules.testcases.models import TestCase


class CoverageService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Single-requirement coverage ────────────────────────────────

    async def compute_coverage(self, requirement_id: UUID) -> RequirementCoverageItem:
        """Compute coverage for a single requirement from TestCase relations."""
        req = await self.session.get(Requirement, requirement_id)
        if not req or req.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")

        tc_q = (
            select(func.count())
            .select_from(TestCase)
            .where(
                TestCase.requirement_id == requirement_id,
                TestCase.deleted_at.is_(None),
            )
        )
        tc_count: int = (await self.session.execute(tc_q)).scalar() or 0

        sn_q = (
            select(func.count())
            .select_from(TestCase)
            .where(
                TestCase.requirement_id == requirement_id,
                TestCase.scene_node_id.is_not(None),
                TestCase.deleted_at.is_(None),
            )
        )
        sn_count: int = (await self.session.execute(sn_q)).scalar() or 0

        if tc_count == 0:
            cov_type = "none"
        elif sn_count > 0:
            cov_type = "full"
        else:
            cov_type = "partial"

        return RequirementCoverageItem(
            requirement_id=req.id,
            req_id=req.req_id,
            title=req.title,
            coverage_type=cov_type,
            test_case_count=tc_count,
            scene_node_count=sn_count,
        )

    # ── Iteration-level matrix ─────────────────────────────────────

    async def get_coverage_matrix(self, iteration_id: UUID) -> dict:
        """Return per-requirement coverage list and aggregated stats."""
        req_q = select(Requirement).where(
            Requirement.iteration_id == iteration_id,
            Requirement.deleted_at.is_(None),
        )
        requirements = list((await self.session.execute(req_q)).scalars().all())

        items: list[RequirementCoverageItem] = []
        full_count = 0
        partial_count = 0
        none_count = 0

        for req in requirements:
            item = await self.compute_coverage(req.id)
            items.append(item)
            if item.coverage_type == "full":
                full_count += 1
            elif item.coverage_type == "partial":
                partial_count += 1
            else:
                none_count += 1

        total = len(requirements)
        coverage_rate = round((full_count + partial_count) / total * 100, 1) if total else 0.0

        stats = CoverageStatsResponse(
            iteration_id=iteration_id,
            total_requirements=total,
            covered_requirements=full_count,
            partially_covered=partial_count,
            uncovered_requirements=none_count,
            coverage_rate=coverage_rate,
        )

        return {"items": [i.model_dump() for i in items], "stats": stats.model_dump()}

    # ── Coverage stats shortcut ────────────────────────────────────

    async def get_coverage_stats(self, iteration_id: UUID) -> CoverageStatsResponse:
        matrix = await self.get_coverage_matrix(iteration_id)
        return CoverageStatsResponse(**matrix["stats"])

    # ── Uncovered requirements ─────────────────────────────────────

    async def get_uncovered_requirements(self, iteration_id: UUID | None = None) -> list[UncoveredRequirementItem]:
        """Return requirements that have zero associated test cases."""
        tc_subq = select(TestCase.requirement_id).where(TestCase.deleted_at.is_(None)).distinct().subquery()
        q = select(Requirement).where(
            Requirement.deleted_at.is_(None),
            Requirement.id.notin_(select(tc_subq.c.requirement_id)),
        )
        if iteration_id:
            q = q.where(Requirement.iteration_id == iteration_id)

        q = q.order_by(Requirement.created_at.desc())
        result = await self.session.execute(q)
        reqs = list(result.scalars().all())
        return [
            UncoveredRequirementItem(
                id=r.id,
                req_id=r.req_id,
                title=r.title,
                status=r.status,
                created_at=r.created_at,
            )
            for r in reqs
        ]

    # ── Explicit coverage record CRUD ──────────────────────────────

    async def upsert_coverage(self, data: CoverageMatrixCreate) -> CoverageMatrix:
        """Create or update a coverage matrix entry (idempotent)."""
        q = select(CoverageMatrix).where(
            CoverageMatrix.requirement_id == data.requirement_id,
            CoverageMatrix.test_case_id == data.test_case_id,
            CoverageMatrix.deleted_at.is_(None),
        )
        existing = (await self.session.execute(q)).scalar_one_or_none()
        if existing:
            existing.coverage_type = data.coverage_type
            existing.scene_node_id = data.scene_node_id
            existing.notes = data.notes
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        entry = CoverageMatrix(**data.model_dump())
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def soft_delete_coverage(self, coverage_id: UUID) -> None:
        entry = await self.session.get(CoverageMatrix, coverage_id)
        if not entry or entry.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coverage entry not found")
        entry.deleted_at = datetime.now(UTC)
        await self.session.commit()
