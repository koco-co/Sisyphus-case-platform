from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.test_cases.validators import validate_case_quality
from app.models.test_case_package_version import TestCasePackageVersion
from app.models.test_point_version import TestPointVersion


def _build_case(point: dict) -> dict:
    case = {
        'module': point.get('module', 'General'),
        'test_point': point.get('name', 'General 主流程校验'),
        'title': f"{point.get('module', 'General')} - {point.get('name', '主流程校验')}",
        'preconditions': '已完成基础主数据准备',
        'steps': [
            '进入对应业务模块',
            '录入满足规则的测试数据',
            '提交并触发处理流程',
        ],
        'expected_results': f"{point.get('module', 'General')} 模块按照既定规则完成处理，并记录可追踪结果",
        'priority': 'P1',
        'tags': [point.get('type', 'main_flow')],
    }
    if 'expected_results_too_vague' in validate_case_quality(case):
        case['expected_results'] = f"{point.get('module', 'General')} 模块处理结果应可追踪且状态变更明确"
    return case


async def generate_case_package_version(db: AsyncSession, task_id: int) -> TestCasePackageVersion | None:
    latest_points = await db.scalar(
        select(TestPointVersion)
        .where(TestPointVersion.task_id == task_id)
        .order_by(TestPointVersion.version_no.desc())
    )
    if latest_points is None:
        return None

    latest_version = await db.scalar(
        select(func.max(TestCasePackageVersion.version_no)).where(TestCasePackageVersion.task_id == task_id)
    )
    next_version = (latest_version or 0) + 1

    points = latest_points.content_json.get('points', [])
    cases = [_build_case(point) for point in points]
    version = TestCasePackageVersion(
        task_id=task_id,
        version_no=next_version,
        status='draft',
        content_json={
            'cases': cases,
            'test_point_version_id': latest_points.id,
        },
        generated_by='system',
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version
