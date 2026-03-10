from collections import defaultdict
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
from app.modules.products.models import Iteration, Requirement
from app.modules.scene_map.models import SceneMap, TestPoint
from app.modules.testcases.models import TestCase


class CoverageService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_product_coverage(self, product_id: UUID) -> dict:
        """Return iteration/requirement coverage data matching the frontend matrix contract."""
        iteration_q = (
            select(Iteration)
            .where(
                Iteration.product_id == product_id,
                Iteration.deleted_at.is_(None),
            )
            .order_by(Iteration.created_at.desc())
        )
        iterations = list((await self.session.execute(iteration_q)).scalars().all())
        if not iterations:
            return {"iterations": []}

        iteration_ids = [iteration.id for iteration in iterations]
        requirement_q = (
            select(Requirement)
            .where(
                Requirement.iteration_id.in_(iteration_ids),
                Requirement.deleted_at.is_(None),
            )
            .order_by(Requirement.created_at.asc())
        )
        requirements = list((await self.session.execute(requirement_q)).scalars().all())
        if not requirements:
            return {
                "iterations": [
                    {
                        "iteration_id": str(iteration.id),
                        "iteration_name": iteration.name,
                        "coverage_rate": 0,
                        "requirement_count": 0,
                        "testcase_count": 0,
                        "uncovered_count": 0,
                        "requirements": [],
                    }
                    for iteration in iterations
                ]
            }

        requirement_ids = [requirement.id for requirement in requirements]
        scene_map_q = (
            select(SceneMap)
            .where(
                SceneMap.requirement_id.in_(requirement_ids),
                SceneMap.deleted_at.is_(None),
            )
            .order_by(SceneMap.created_at.asc())
        )
        scene_maps = list((await self.session.execute(scene_map_q)).scalars().all())
        scene_map_by_requirement = {scene_map.requirement_id: scene_map for scene_map in scene_maps}

        scene_map_ids = [scene_map.id for scene_map in scene_maps]
        test_points: list[TestPoint] = []
        if scene_map_ids:
            test_point_q = (
                select(TestPoint)
                .where(
                    TestPoint.scene_map_id.in_(scene_map_ids),
                    TestPoint.deleted_at.is_(None),
                )
                .order_by(TestPoint.sort_order.asc(), TestPoint.created_at.asc())
            )
            test_points = list((await self.session.execute(test_point_q)).scalars().all())

        test_cases_q = (
            select(TestCase)
            .where(
                TestCase.requirement_id.in_(requirement_ids),
                TestCase.deleted_at.is_(None),
            )
            .order_by(TestCase.created_at.asc())
        )
        test_cases = list((await self.session.execute(test_cases_q)).scalars().all())

        requirements_by_iteration: dict[UUID, list] = defaultdict(list)
        for requirement in requirements:
            requirements_by_iteration[requirement.iteration_id].append(requirement)

        test_points_by_scene_map: dict[UUID, list[TestPoint]] = defaultdict(list)
        for test_point in test_points:
            test_points_by_scene_map[test_point.scene_map_id].append(test_point)

        cases_by_requirement: dict[UUID, list[TestCase]] = defaultdict(list)
        cases_by_test_point: dict[UUID, list[TestCase]] = defaultdict(list)
        for test_case in test_cases:
            cases_by_requirement[test_case.requirement_id].append(test_case)
            if test_case.scene_node_id:
                cases_by_test_point[test_case.scene_node_id].append(test_case)

        payload_iterations = []
        for iteration in iterations:
            iteration_requirements = requirements_by_iteration.get(iteration.id, [])
            requirement_items = []
            uncovered_count = 0

            for requirement in iteration_requirements:
                scene_map = scene_map_by_requirement.get(requirement.id)
                requirement_test_points = (
                    test_points_by_scene_map.get(scene_map.id, []) if scene_map else []
                )
                requirement_test_cases = cases_by_requirement.get(requirement.id, [])
                point_items = []

                for test_point in requirement_test_points:
                    point_cases = cases_by_test_point.get(test_point.id, [])
                    point_items.append(
                        {
                            "id": str(test_point.id),
                            "title": test_point.title,
                            "priority": test_point.priority,
                            "case_count": len(point_cases),
                            "cases": [
                                {
                                    "id": str(test_case.id),
                                    "case_id": test_case.case_id,
                                    "title": test_case.title,
                                    "status": test_case.status,
                                }
                                for test_case in point_cases
                            ],
                        }
                    )

                if not requirement_test_cases:
                    coverage_status = "none"
                    uncovered_count += 1
                elif requirement_test_points and all(
                    cases_by_test_point.get(test_point.id) for test_point in requirement_test_points
                ):
                    coverage_status = "full"
                else:
                    coverage_status = "partial"

                requirement_items.append(
                    {
                        "id": str(requirement.id),
                        "req_id": requirement.req_id,
                        "title": requirement.title,
                        "coverage_status": coverage_status,
                        "test_points": point_items,
                    }
                )

            requirement_count = len(iteration_requirements)
            coverage_rate = (
                round((requirement_count - uncovered_count) / requirement_count * 100)
                if requirement_count
                else 0
            )
            payload_iterations.append(
                {
                    "iteration_id": str(iteration.id),
                    "iteration_name": iteration.name,
                    "coverage_rate": coverage_rate,
                    "requirement_count": requirement_count,
                    "testcase_count": sum(
                        len(cases_by_requirement.get(requirement.id, []))
                        for requirement in iteration_requirements
                    ),
                    "uncovered_count": uncovered_count,
                    "requirements": requirement_items,
                }
            )

        return {"iterations": payload_iterations}

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
