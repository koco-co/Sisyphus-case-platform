"""导出文件生成异步任务 — 生成 Excel / PDF 导出包。"""

from __future__ import annotations

import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.export_task.generate_export", max_retries=3)
def generate_export(self, export_job_id: str, format_type: str, test_case_ids: list[str]) -> dict:
    """生成用例导出文件。

    Args:
        export_job_id: 导出任务 ID
        format_type: 导出格式 (excel / pdf / csv)
        test_case_ids: 要导出的用例 ID 列表
    """
    self.update_state(state="STARTED", meta={"step": "querying", "progress": 0})

    try:
        self.update_state(
            state="STARTED",
            meta={"step": "generating", "progress": 30, "total_cases": len(test_case_ids)},
        )

        # TODO: 查询用例数据 → 生成文件 → 上传到 MinIO
        logger.info(
            "导出任务完成: export_job_id=%s, format=%s, cases=%d",
            export_job_id,
            format_type,
            len(test_case_ids),
        )

        self.update_state(state="STARTED", meta={"step": "complete", "progress": 100})
        return {
            "status": "success",
            "export_job_id": export_job_id,
            "format": format_type,
            "total_cases": len(test_case_ids),
        }

    except Exception as exc:
        logger.error("导出任务失败 export_job_id=%s: %s", export_job_id, exc, exc_info=True)
        try:
            self.retry(exc=exc, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            return {"status": "failed", "error": str(exc)}
    return {"status": "failed", "error": "unknown"}
