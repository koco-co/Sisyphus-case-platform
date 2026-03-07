from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_asset import KnowledgeAsset
from app.models.requirement_task import RequirementTask
from app.models.structured_requirement_version import StructuredRequirementVersion
from app.models.test_case_package_version import TestCasePackageVersion
from app.models.test_point_version import TestPointVersion


async def build_coverage_report(db: AsyncSession, task_id: int) -> dict | None:
    task = await db.scalar(select(RequirementTask).where(RequirementTask.id == task_id))
    if task is None:
        return None

    structured = await db.scalar(
        select(StructuredRequirementVersion)
        .where(StructuredRequirementVersion.task_id == task_id)
        .order_by(StructuredRequirementVersion.version_no.desc())
    )
    test_points = await db.scalar(
        select(TestPointVersion)
        .where(TestPointVersion.task_id == task_id)
        .order_by(TestPointVersion.version_no.desc())
    )
    case_package = await db.scalar(
        select(TestCasePackageVersion)
        .where(TestCasePackageVersion.task_id == task_id)
        .order_by(TestCasePackageVersion.version_no.desc())
    )

    structured_modules = len((structured.content_json if structured else {}).get('modules', []))
    point_count = len((test_points.content_json if test_points else {}).get('points', []))
    case_count = len((case_package.content_json if case_package else {}).get('cases', []))
    denominator = max(structured_modules, 1)
    coverage_ratio = min(case_count / denominator, 1.0) if case_count else 0.0

    return {
        'task_id': task_id,
        'structured_modules': structured_modules,
        'test_points': point_count,
        'generated_cases': case_count,
        'coverage_ratio': coverage_ratio,
    }


async def publish_task(db: AsyncSession, task_id: int) -> dict | None:
    task = await db.scalar(select(RequirementTask).where(RequirementTask.id == task_id))
    if task is None:
        return None

    case_package = await db.scalar(
        select(TestCasePackageVersion)
        .where(TestCasePackageVersion.task_id == task_id, TestCasePackageVersion.status == 'approved')
        .order_by(TestCasePackageVersion.version_no.desc())
    )
    if case_package is None:
        return {'error': 'approved_case_package_missing'}

    task.task_status = 'published'
    task.current_stage = 'published'

    asset = KnowledgeAsset(
        task_id=task_id,
        asset_type='case_asset',
        title=f'{task.title} 发布测试包',
        summary='由发布动作自动沉淀的高质量测试资产',
        content_json=case_package.content_json,
        status='curated',
        quality_level='curated',
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    await db.refresh(task)

    return {
        'task_id': task.id,
        'task_status': task.task_status,
        'knowledge_asset_created': True,
        'knowledge_asset_id': asset.id,
    }
