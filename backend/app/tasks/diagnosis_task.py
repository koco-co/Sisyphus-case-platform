"""诊断扫描异步任务 — 对需求文档执行 6 维度风险扫描。"""

from __future__ import annotations

import asyncio
import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.diagnosis_task.run_diagnosis_scan", max_retries=3)
def run_diagnosis_scan(self, requirement_id: str, requirement_text: str) -> dict:
    """对需求文档执行异步诊断扫描。

    Args:
        requirement_id: 需求 ID
        requirement_text: 需求文档文本
    """
    self.update_state(state="STARTED", meta={"step": "scanning", "progress": 0})

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            risks = loop.run_until_complete(_do_scan(requirement_text))
        finally:
            loop.close()

        self.update_state(state="STARTED", meta={"step": "saving", "progress": 80})

        logger.info("诊断扫描完成: requirement_id=%s, risks=%d", requirement_id, len(risks))
        return {"status": "success", "requirement_id": requirement_id, "risk_count": len(risks), "risks": risks}

    except Exception as exc:
        logger.error("诊断扫描失败 requirement_id=%s: %s", requirement_id, exc, exc_info=True)
        try:
            self.retry(exc=exc, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            return {"status": "failed", "error": str(exc)}
    return {"status": "failed", "error": "unknown"}


async def _do_scan(requirement_text: str) -> list[dict]:
    """执行实际扫描逻辑。"""
    from app.engine.diagnosis.scanner import scan_requirement

    return await scan_requirement(requirement_text)
