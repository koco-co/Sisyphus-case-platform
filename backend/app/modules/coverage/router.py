import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.dependencies import AsyncSessionDep
from app.modules.coverage.schemas import (
    CoverageMatrixCreate,
    CoverageMatrixResponse,
    CoverageStatsResponse,
    UncoveredRequirementItem,
)
from app.modules.coverage.service import CoverageService

router = APIRouter(prefix="/coverage", tags=["coverage"])


@router.get("/product/{product_id}")
async def get_product_coverage(product_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    """Return product-level coverage data for the coverage dashboard."""
    svc = CoverageService(session)
    return await svc.get_product_coverage(product_id)


@router.get("/{iteration_id}")
async def get_coverage_matrix(iteration_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    """Return per-requirement coverage matrix for an iteration."""
    svc = CoverageService(session)
    return await svc.get_coverage_matrix(iteration_id)


@router.get("/{iteration_id}/stats", response_model=CoverageStatsResponse)
async def get_coverage_stats(iteration_id: uuid.UUID, session: AsyncSessionDep) -> CoverageStatsResponse:
    """Return aggregated coverage statistics for an iteration."""
    svc = CoverageService(session)
    return await svc.get_coverage_stats(iteration_id)


@router.get("/uncovered/list", response_model=list[UncoveredRequirementItem])
async def get_uncovered_requirements(
    session: AsyncSessionDep,
    iteration_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[UncoveredRequirementItem]:
    """Return requirements with no associated test cases."""
    svc = CoverageService(session)
    return await svc.get_uncovered_requirements(iteration_id)


@router.post("", response_model=CoverageMatrixResponse, status_code=status.HTTP_201_CREATED)
async def upsert_coverage(data: CoverageMatrixCreate, session: AsyncSessionDep) -> CoverageMatrixResponse:
    """Create or update a coverage matrix entry (idempotent)."""
    svc = CoverageService(session)
    entry = await svc.upsert_coverage(data)
    return CoverageMatrixResponse.model_validate(entry)


@router.delete("/{coverage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coverage(coverage_id: uuid.UUID, session: AsyncSessionDep) -> None:
    svc = CoverageService(session)
    await svc.soft_delete_coverage(coverage_id)
