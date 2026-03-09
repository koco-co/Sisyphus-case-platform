"""Celery 任务状态查询 — Router"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.celery_app import celery_app
from app.modules.import_clean.schemas import TaskStatusResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """查询 Celery 异步任务状态和进度。"""
    result = celery_app.AsyncResult(task_id)

    if result.state == "PENDING":
        return TaskStatusResponse(task_id=task_id, status="PENDING", progress=0, step=None, result=None)

    if result.state == "STARTED":
        meta = result.info or {}
        return TaskStatusResponse(
            task_id=task_id,
            status="STARTED",
            progress=meta.get("progress", 0),
            step=meta.get("step"),
            result=None,
        )

    if result.state == "SUCCESS":
        return TaskStatusResponse(
            task_id=task_id,
            status="SUCCESS",
            progress=100,
            step="complete",
            result=result.result if isinstance(result.result, dict) else None,
        )

    if result.state == "FAILURE":
        error_msg = str(result.result) if result.result else "未知错误"
        return TaskStatusResponse(
            task_id=task_id,
            status="FAILURE",
            progress=0,
            step="failed",
            result={"error": error_msg},
        )

    # RETRY 或其他自定义状态
    meta = result.info if isinstance(result.info, dict) else {}
    return TaskStatusResponse(
        task_id=task_id,
        status=result.state,
        progress=meta.get("progress", 0),
        step=meta.get("step"),
        result=meta,
    )


@router.post("/{task_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_task(task_id: str) -> None:
    """撤销正在执行或排队中的任务。"""
    result = celery_app.AsyncResult(task_id)
    if result.state in ("SUCCESS", "FAILURE"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"任务已结束，状态: {result.state}")
    celery_app.control.revoke(task_id, terminate=True)
