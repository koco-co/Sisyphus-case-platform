from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement_task import RequirementTask
from app.models.source_document import SourceDocument


async def run_ingestion_job(db: AsyncSession, task_id: int) -> RequirementTask | None:
    task = await db.scalar(select(RequirementTask).where(RequirementTask.id == task_id))
    if task is None:
        return None

    documents = (
        await db.execute(
            select(SourceDocument).where(SourceDocument.task_id == task_id).order_by(SourceDocument.id.asc())
        )
    ).scalars().all()

    extracted_chunks = [document.extracted_text for document in documents if document.extracted_text]
    task.input_summary = "\n\n".join(extracted_chunks) if extracted_chunks else None
    task.input_quality_score = (
        sum(document.quality_score or 0 for document in documents) / len(documents)
        if documents
        else None
    )
    task.task_status = "ready_for_structuring"
    task.current_stage = "structuring"

    await db.commit()
    await db.refresh(task)
    return task
