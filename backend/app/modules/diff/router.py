import uuid

from fastapi import APIRouter

from app.core.dependencies import AsyncSessionDep
from app.modules.diff.schemas import (
    DiffRequest,
    DiffResponse,
    RegenerateRequest,
    RegenerateResponse,
    SuggestionResponse,
)
from app.modules.diff.service import DiffService

router = APIRouter(prefix="/diff", tags=["diff"])


@router.post("/{requirement_id}/compute", response_model=DiffResponse)
async def compute_diff(
    requirement_id: uuid.UUID,
    data: DiffRequest,
    session: AsyncSessionDep,
) -> DiffResponse:
    """计算两个版本间的 Diff 并自动标记受影响的测试点和用例。"""
    svc = DiffService(session)
    diff = await svc.compute_diff(requirement_id, data.version_from, data.version_to)
    return DiffResponse.model_validate(diff)


@router.get("/{requirement_id}/history")
async def list_diffs(requirement_id: uuid.UUID, session: AsyncSessionDep) -> list[dict]:
    """获取需求的 Diff 历史记录。"""
    svc = DiffService(session)
    diffs = await svc.get_diffs(requirement_id)
    return [
        {
            "id": str(d.id),
            "version_from": d.version_from,
            "version_to": d.version_to,
            "impact_level": d.impact_level,
            "summary": d.summary,
            "created_at": d.created_at.isoformat() if d.created_at else "",
        }
        for d in diffs
    ]


@router.get("/{requirement_id}/latest", response_model=DiffResponse | None)
async def get_latest_diff(requirement_id: uuid.UUID, session: AsyncSessionDep) -> DiffResponse | None:
    """获取需求的最新 Diff 记录。"""
    svc = DiffService(session)
    diff = await svc.get_latest_diff(requirement_id)
    if not diff:
        return None
    return DiffResponse.model_validate(diff)


@router.get("/{requirement_id}/suggestions", response_model=SuggestionResponse)
async def suggest_test_points(
    requirement_id: uuid.UUID,
    session: AsyncSessionDep,
) -> SuggestionResponse:
    """基于最新 Diff 变更建议新增测试点 (B-M07-06)。"""
    svc = DiffService(session)
    suggestions = await svc.suggest_test_points(requirement_id)
    return SuggestionResponse(suggestions=suggestions, count=len(suggestions))


@router.post("/{requirement_id}/regenerate", response_model=RegenerateResponse)
async def regenerate_cases(
    requirement_id: uuid.UUID,
    data: RegenerateRequest,
    session: AsyncSessionDep,
) -> RegenerateResponse:
    """一键重新生成受影响的用例 (B-M07-10)。"""
    svc = DiffService(session)
    cases = await svc.regenerate_affected_cases(requirement_id, data.test_point_ids)
    return RegenerateResponse(regenerated_cases=cases, count=len(cases))
