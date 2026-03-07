from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.structured_requirement_version import StructuredRequirementVersion
from app.models.test_point_version import TestPointVersion


def _build_points(structured_content: dict) -> list[dict[str, str]]:
    modules = structured_content.get('modules', []) if structured_content else []
    points: list[dict[str, str]] = []
    for module in modules:
        module_name = module.get('name', 'General')
        module_summary = module.get('summary', '')
        points.append({
            'module': module_name,
            'name': f'{module_name} 主流程校验',
            'type': 'main_flow',
            'summary': module_summary,
        })
    return points or [{'module': 'General', 'name': 'General 主流程校验', 'type': 'main_flow', 'summary': ''}]


async def generate_test_point_version(db: AsyncSession, task_id: int) -> TestPointVersion | None:
    latest_structured = await db.scalar(
        select(StructuredRequirementVersion)
        .where(StructuredRequirementVersion.task_id == task_id)
        .order_by(StructuredRequirementVersion.version_no.desc())
    )
    if latest_structured is None:
        return None

    latest_version = await db.scalar(
        select(func.max(TestPointVersion.version_no)).where(TestPointVersion.task_id == task_id)
    )
    next_version = (latest_version or 0) + 1

    version = TestPointVersion(
        task_id=task_id,
        version_no=next_version,
        status='draft',
        content_json={
            'points': _build_points(latest_structured.content_json),
            'structured_version_id': latest_structured.id,
        },
        generated_by='system',
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version
