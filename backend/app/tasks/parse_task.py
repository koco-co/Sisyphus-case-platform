"""文档解析异步任务 — 对上传文件执行后台解析。"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.parse_task.parse_import_file", max_retries=3)
def parse_import_file(self, job_id: str, file_content_b64: str, file_type: str) -> dict:
    """解析导入文件（CSV / Excel / Markdown）。

    Args:
        job_id: ImportJob ID
        file_content_b64: base64 编码的文件内容
        file_type: 文件类型 (csv / excel / markdown)
    """
    import base64

    self.update_state(state="STARTED", meta={"step": "parsing", "progress": 0})

    try:
        data = base64.b64decode(file_content_b64)

        if file_type == "csv":
            from app.engine.import_clean.csv_parser import parse_csv_bytes

            records = parse_csv_bytes(data)
        elif file_type == "excel":
            from app.engine.import_clean.excel_parser import parse_excel

            records = parse_excel(data)
        elif file_type == "markdown":
            from app.engine.import_clean.md_parser import parse_markdown_bytes

            records = parse_markdown_bytes(data)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")

        self.update_state(state="STARTED", meta={"step": "saving", "progress": 50})

        # 在同步上下文中运行异步持久化
        asyncio.get_event_loop().run_until_complete(_persist_records(UUID(job_id), records))

        self.update_state(state="STARTED", meta={"step": "complete", "progress": 100})
        return {"status": "success", "total_records": len(records)}

    except Exception as exc:
        logger.error("解析任务失败 job_id=%s: %s", job_id, exc, exc_info=True)
        try:
            self.retry(exc=exc, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            _mark_job_failed_sync(UUID(job_id), str(exc))
            return {"status": "failed", "error": str(exc)}
    return {"status": "failed", "error": "unknown"}


async def _persist_records(job_id: UUID, records: list[dict]) -> None:
    """将解析结果持久化到数据库。"""
    from app.core.database import get_async_session_context
    from app.modules.import_clean.models import ImportJob, ImportRecord

    async with get_async_session_context() as session:
        for record in records:
            row_num = record.pop("_row_number", 0)
            title = record.get("title") or record.get("标题") or record.get("用例标题", "")
            db_record = ImportRecord(
                job_id=job_id,
                row_number=row_num,
                raw_data=record,
                original_title=title or None,
                status="pending",
            )
            session.add(db_record)

        job = await session.get(ImportJob, job_id)
        if job:
            job.total_records = len(records)
            job.status = "mapping"


def _mark_job_failed_sync(job_id: UUID, error: str) -> None:
    """同步标记任务失败。"""
    asyncio.get_event_loop().run_until_complete(_mark_job_failed(job_id, error))


async def _mark_job_failed(job_id: UUID, error: str) -> None:
    from app.core.database import get_async_session_context
    from app.modules.import_clean.models import ImportJob

    async with get_async_session_context() as session:
        job = await session.get(ImportJob, job_id)
        if job:
            job.status = "failed"
            job.error_message = error
