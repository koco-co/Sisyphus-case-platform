"""Diff 计算异步任务 — 对需求变更执行文本级 + 语义级 Diff 分析。"""

from __future__ import annotations

import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.diff_task.compute_diff", max_retries=3)
def compute_diff(self, diff_job_id: str, old_text: str, new_text: str) -> dict:
    """计算两个版本的需求文本差异。

    Args:
        diff_job_id: Diff 任务 ID
        old_text: 旧版本文本
        new_text: 新版本文本
    """
    self.update_state(state="STARTED", meta={"step": "text_diff", "progress": 0})

    try:
        # 阶段 1: 文本级 Diff（Myers / difflib）
        from difflib import unified_diff

        text_diff = list(
            unified_diff(
                old_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile="old",
                tofile="new",
            )
        )

        self.update_state(state="STARTED", meta={"step": "semantic_diff", "progress": 50})

        # 阶段 2: 语义级分析（TODO: 接入 engine/diff LLM 分析）
        logger.info("Diff 计算完成: diff_job_id=%s, changes=%d", diff_job_id, len(text_diff))

        return {
            "status": "success",
            "diff_job_id": diff_job_id,
            "text_diff_lines": len(text_diff),
            "text_diff": "".join(text_diff[:100]),
        }

    except Exception as exc:
        logger.error("Diff 计算失败 diff_job_id=%s: %s", diff_job_id, exc, exc_info=True)
        try:
            self.retry(exc=exc, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            return {"status": "failed", "error": str(exc)}
    return {"status": "failed", "error": "unknown"}
