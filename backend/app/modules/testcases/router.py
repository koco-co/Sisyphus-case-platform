import math
import uuid
from typing import Annotated, Any, cast

from fastapi import APIRouter, File, Query, UploadFile, status

from app.core.dependencies import AsyncSessionDep
from app.modules.testcases.import_service import TestCaseImportService
from app.modules.testcases.schemas import (
    FolderCreate,
    FolderReorderRequest,
    FolderResponse,
    FolderUpdate,
    MoveCasesRequest,
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
from app.modules.testcases.service import FolderService, TestCaseService

router = APIRouter(prefix="/testcases", tags=["testcases"])


# ── Import endpoints ───────────────────────────────────────────────


@router.post("/import/parse-file")
async def parse_import_file(
    session: AsyncSessionDep,
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any]:
    """Parse an uploaded file (xlsx/csv/json/xmind) for import preview.

    Returns columns, first-5 preview rows, full row list, auto-mapping, and
    whether the file matches the standard template.
    """
    svc = TestCaseImportService(session)
    return await svc.parse_file(file)


@router.post("/import/check-duplicates")
async def check_import_duplicates(
    data: dict[str, Any],
    session: AsyncSessionDep,
) -> list[dict[str, Any]]:
    """Check which cases in the payload already exist in the target folder.

    Body: ``{"cases": [{title, ...}, ...], "folder_id": "<uuid> | null"}``
    Returns a list of duplicate-info objects (index, title, existing_id).
    """
    svc = TestCaseImportService(session)
    folder_id = uuid.UUID(data["folder_id"]) if data.get("folder_id") else None
    return await svc.check_duplicates(data["cases"], folder_id)


@router.post("/import/batch")
async def batch_import_cases(
    data: dict[str, Any],
    session: AsyncSessionDep,
) -> dict[str, int]:
    """Batch-import cases with per-case duplicate strategies.

    Body::

        {
            "cases": [{title, steps, expected_result, ...}, ...],
            "folder_id": "<uuid> | null",
            "per_case_strategies": {"0": "skip", "3": "overwrite", "5": "rename"}
        }

    Returns import stats: imported / skipped / overwritten / renamed.
    """
    svc = TestCaseImportService(session)
    folder_id = uuid.UUID(data["folder_id"]) if data.get("folder_id") else None
    per_case_strategies = {int(k): v for k, v in data.get("per_case_strategies", {}).items()}
    return await svc.batch_import(data["cases"], folder_id, per_case_strategies)


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
        by_status=[
            StatusCountItem(
                status=str(item["status"]),
                count=cast(int, item["count"]),
            )
            for item in by_status
        ],
    )


@router.get("/clean/stats")
async def get_clean_stats(session: AsyncSessionDep) -> dict:
    """获取历史导入清洗用例的统计数据（按 clean_status 分组）。"""
    from sqlalchemy import func, select

    from app.modules.testcases.models import TestCase

    q = (
        select(TestCase.clean_status, func.count().label("count"), func.avg(TestCase.quality_score).label("avg_score"))
        .where(TestCase.deleted_at.is_(None), TestCase.source == "imported")
        .group_by(TestCase.clean_status)
    )
    result = await session.execute(q)
    rows = result.all()
    total_q = select(func.count()).where(TestCase.deleted_at.is_(None), TestCase.source == "imported")
    total = (await session.execute(total_q)).scalar() or 0
    by_status = [
        {"status": r.clean_status or "raw", "count": r.count, "avg_score": round(r.avg_score or 0, 1)} for r in rows
    ]
    return {"total": total, "by_status": by_status}


@router.post("/batch-status")
async def batch_update_status(data: TestCaseBatchAction, session: AsyncSessionDep) -> dict[str, int]:
    svc = TestCaseService(session)
    count = await svc.batch_update_status(data.case_ids, data.status)
    return {"updated": count}


@router.get("/module-paths")
async def get_module_paths(session: AsyncSessionDep) -> list[dict]:
    """返回所有唯一 module_path 构成的目录树，含各节点用例数量。"""
    svc = TestCaseService(session)
    return await svc.get_module_paths()


# ── CRUD ───────────────────────────────────────────────────────────


@router.get("", response_model=TestCaseListResponse)
async def list_cases(
    session: AsyncSessionDep,
    requirement_id: uuid.UUID | None = None,
    scene_node_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    clean_status: str | None = None,
    priority: str | None = None,
    case_type: str | None = None,
    source: str | None = None,
    keyword: str | None = None,
    module_path: str | None = None,
    folder_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TestCaseListResponse:
    svc = TestCaseService(session)
    cases, total = await svc.list_cases(
        requirement_id=requirement_id,
        scene_node_id=scene_node_id,
        status_filter=status_filter,
        clean_status=clean_status,
        priority=priority,
        case_type=case_type,
        source=source,
        keyword=keyword,
        module_path=module_path,
        folder_id=folder_id,
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


# ── Folder CRUD ────────────────────────────────────────────────────


@router.get("/folders/tree")
async def get_folder_tree(session: AsyncSessionDep) -> list[dict]:
    svc = FolderService(session)
    return await svc.get_tree()


@router.post("/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(data: FolderCreate, session: AsyncSessionDep) -> FolderResponse:
    svc = FolderService(session)
    folder = await svc.create_folder(data.name, data.parent_id)
    count = await svc.get_case_count(folder.id)
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        sort_order=folder.sort_order,
        level=folder.level,
        is_system=folder.is_system,
        case_count=count,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
    )


@router.patch("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(folder_id: uuid.UUID, data: FolderUpdate, session: AsyncSessionDep) -> FolderResponse:
    svc = FolderService(session)
    folder = await svc.update_folder(folder_id, data.name, data.sort_order)
    count = await svc.get_case_count(folder.id)
    return FolderResponse(
        id=folder.id,
        name=folder.name,
        parent_id=folder.parent_id,
        sort_order=folder.sort_order,
        level=folder.level,
        is_system=folder.is_system,
        case_count=count,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
    )


@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: uuid.UUID, session: AsyncSessionDep) -> dict:
    svc = FolderService(session)
    return await svc.delete_folder(folder_id)


@router.post("/folders/move-cases")
async def move_cases_to_folder(data: MoveCasesRequest, session: AsyncSessionDep) -> dict:
    svc = FolderService(session)
    count = await svc.move_cases(data.case_ids, data.folder_id)
    return {"moved": count}


@router.post("/folders/reorder")
async def reorder_folders(data: FolderReorderRequest, session: AsyncSessionDep) -> dict:
    svc = FolderService(session)
    await svc.batch_reorder([{"id": item.id, "sort_order": item.sort_order} for item in data.items])
    return {"ok": True}


@router.post("/folders/init-from-products")
async def init_folders_from_products(session: AsyncSessionDep) -> dict:
    """根据产品/迭代/需求结构自动初始化系统目录树（幂等）。"""
    svc = FolderService(session)
    return await svc.init_from_products()
