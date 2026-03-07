from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.integrations.exporters import export_markdown
from app.models.integration_sync_record import IntegrationSyncRecord
from app.models.requirement_task import RequirementTask
from app.models.test_case_package_version import TestCasePackageVersion


async def sync_task(db: AsyncSession, task_id: int, provider: str) -> IntegrationSyncRecord | None:
    task = await db.scalar(select(RequirementTask).where(RequirementTask.id == task_id))
    if task is None:
        return None

    case_package = await db.scalar(
        select(TestCasePackageVersion)
        .where(TestCasePackageVersion.task_id == task_id)
        .order_by(TestCasePackageVersion.version_no.desc())
    )

    output_path = None
    status = 'completed'
    if provider == 'markdown':
        output_path = export_markdown(task_id, case_package.content_json if case_package else {})
    else:
        status = 'queued'

    record = IntegrationSyncRecord(
        task_id=task_id,
        provider=provider,
        status=status,
        output_path=output_path,
        message='同步完成' if status == 'completed' else '同步已排队',
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
