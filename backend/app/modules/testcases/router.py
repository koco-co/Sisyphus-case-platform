import math
import uuid

from fastapi import APIRouter, Query, status

from app.core.dependencies import AsyncSessionDep
from app.modules.testcases.schemas import (
    ReviewRequest,
    StatusCountItem,
    TestCaseBatchAction,
    TestCaseCreate,
    TestCaseListResponse,
    TestCaseResponse,
    TestCaseStatsResponse,
    TestCaseUpdate,
    TestCaseVersionResponse,
    TraceabilityResponse,
)
from app.modules.testcases.service import TestCaseService

router = APIRouter(prefix="/testcases", tags=["testcases"])


# ── Static paths (must precede /{case_id}) ─────────────────────────


@router.get("/stats", response_model=TestCaseStatsResponse)
async def get_stats(
    session: AsyncSessionDep,
    requirement_id: uuid.UUID | None = None,
) -> TestCaseStatsResponse:
    svc = TestCaseService(session)
    total, by_status = await svc.count_by_status(requirement_id)
    return TestCaseStatsResponse(
        total=total,
        by_status=[StatusCountItem(**item) for item in by_status],
    )


@router.post("/batch-status")
async def batch_update_status(data: TestCaseBatchAction, session: AsyncSessionDep) -> dict[str, int]:
    svc = TestCaseService(session)
    count = await svc.batch_update_status(data.case_ids, data.status)
    return {"updated": count}


# ── CRUD ───────────────────────────────────────────────────────────


@router.get("", response_model=TestCaseListResponse)
async def list_cases(
    session: AsyncSessionDep,
    requirement_id: uuid.UUID | None = None,
    scene_node_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = None,
    case_type: str | None = None,
    source: str | None = None,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TestCaseListResponse:
    svc = TestCaseService(session)
    cases, total = await svc.list_cases(
        requirement_id=requirement_id,
        scene_node_id=scene_node_id,
        status_filter=status_filter,
        priority=priority,
        case_type=case_type,
        source=source,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    items = [TestCaseResponse.model_validate(tc) for tc in cases]
    return TestCaseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{case_id}", response_model=TestCaseResponse)
async def get_case(case_id: uuid.UUID, session: AsyncSessionDep) -> TestCaseResponse:
    svc = TestCaseService(session)
    tc = await svc.get_case(case_id)
    return TestCaseResponse.model_validate(tc)


@router.post("", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(data: TestCaseCreate, session: AsyncSessionDep) -> TestCaseResponse:
    svc = TestCaseService(session)
    tc = await svc.create_case(data)
    return TestCaseResponse.model_validate(tc)


@router.put("/{case_id}", response_model=TestCaseResponse)
async def update_case(case_id: uuid.UUID, data: TestCaseUpdate, session: AsyncSessionDep) -> TestCaseResponse:
    svc = TestCaseService(session)
    tc = await svc.update_case(case_id, data)
    return TestCaseResponse.model_validate(tc)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: uuid.UUID, session: AsyncSessionDep) -> None:
    svc = TestCaseService(session)
    await svc.soft_delete_case(case_id)


# ── Version management (B-M06-05) ─────────────────────────────────


@router.get("/{case_id}/versions", response_model=list[TestCaseVersionResponse])
async def list_versions(case_id: uuid.UUID, session: AsyncSessionDep) -> list[TestCaseVersionResponse]:
    svc = TestCaseService(session)
    await svc.get_case(case_id)  # validate exists
    versions = await svc.list_versions(case_id)
    return [TestCaseVersionResponse.model_validate(v) for v in versions]


@router.get("/{case_id}/versions/{version}", response_model=TestCaseVersionResponse)
async def get_version(case_id: uuid.UUID, version: int, session: AsyncSessionDep) -> TestCaseVersionResponse:
    svc = TestCaseService(session)
    ver = await svc.get_version(case_id, version)
    return TestCaseVersionResponse.model_validate(ver)


# ── Review workflow (B-M06-06) ─────────────────────────────────────


@router.post("/{case_id}/submit-review", response_model=TestCaseResponse)
async def submit_for_review(case_id: uuid.UUID, session: AsyncSessionDep) -> TestCaseResponse:
    svc = TestCaseService(session)
    tc = await svc.submit_for_review(case_id)
    return TestCaseResponse.model_validate(tc)


@router.post("/{case_id}/approve", response_model=TestCaseResponse)
async def approve_case(case_id: uuid.UUID, data: ReviewRequest, session: AsyncSessionDep) -> TestCaseResponse:
    svc = TestCaseService(session)
    if not data.reviewer_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="reviewer_id is required")
    tc = await svc.approve_case(case_id, data.reviewer_id)
    return TestCaseResponse.model_validate(tc)


@router.post("/{case_id}/reject", response_model=TestCaseResponse)
async def reject_case(case_id: uuid.UUID, data: ReviewRequest, session: AsyncSessionDep) -> TestCaseResponse:
    svc = TestCaseService(session)
    if not data.reviewer_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="reviewer_id is required")
    tc = await svc.reject_case(case_id, data.reviewer_id, data.reason)
    return TestCaseResponse.model_validate(tc)


# ── Traceability (B-M06-07) ───────────────────────────────────────


@router.get("/{case_id}/traceability", response_model=TraceabilityResponse)
async def get_traceability(case_id: uuid.UUID, session: AsyncSessionDep) -> TraceabilityResponse:
    svc = TestCaseService(session)
    chain = await svc.get_traceability(case_id)

    def _to_dict(obj: object) -> dict | None:
        if obj is None:
            return None
        from app.shared.base_schema import BaseResponse

        return BaseResponse.model_validate(obj).model_dump()

    return TraceabilityResponse(
        test_case=TestCaseResponse.model_validate(chain["test_case"]),
        test_point=_to_dict(chain.get("test_point")),
        scene_map=_to_dict(chain.get("scene_map")),
        requirement=_to_dict(chain.get("requirement")),
        iteration=_to_dict(chain.get("iteration")),
        product=_to_dict(chain.get("product")),
    )
