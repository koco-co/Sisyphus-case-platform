from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement_task import RequirementTask
from app.models.structured_requirement_version import StructuredRequirementVersion


def _build_modules(summary: str | None) -> list[dict[str, str]]:
    if not summary:
        return [{"name": "General", "summary": ""}]

    lines = [line.strip() for line in summary.splitlines() if line.strip()]
    heading = next((line.lstrip('#').strip() for line in lines if line.startswith('#')), None)
    body = " ".join(line for line in lines if not line.startswith('#')).strip()

    return [{
        "name": heading or "General",
        "summary": body,
    }]


async def generate_structured_requirement_version(db: AsyncSession, task_id: int) -> StructuredRequirementVersion | None:
    task = await db.scalar(select(RequirementTask).where(RequirementTask.id == task_id))
    if task is None:
        return None

    latest_version = await db.scalar(
        select(func.max(StructuredRequirementVersion.version_no)).where(StructuredRequirementVersion.task_id == task_id)
    )
    next_version = (latest_version or 0) + 1

    version = StructuredRequirementVersion(
        task_id=task.id,
        version_no=next_version,
        status='draft',
        content_json={
            'modules': _build_modules(task.input_summary),
            'raw_summary': task.input_summary,
        },
        generated_by='system',
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version
