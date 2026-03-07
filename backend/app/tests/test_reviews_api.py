import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.project import Project
from app.models.requirement_task import RequirementTask
from app.models.structured_requirement_version import StructuredRequirementVersion
from app.models.test_case_package_version import TestCasePackageVersion
from app.models.test_point_version import TestPointVersion
from app.models.knowledge_asset import KnowledgeAsset

TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'
TEST_TABLES = [
    Project.__table__,
    RequirementTask.__table__,
    StructuredRequirementVersion.__table__,
    TestPointVersion.__table__,
    TestCasePackageVersion.__table__,
    KnowledgeAsset.__table__,
]


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=TEST_TABLES))

    async with async_session() as session:
        project = Project(name='审核项目', description='审核与发布测试')
        session.add(project)
        await session.flush()

        task = RequirementTask(
            project_id=project.id,
            title='Publish me',
            source_type='md',
            current_stage='review',
            task_status='case_package_ready',
        )
        session.add(task)
        await session.flush()

        session.add(
            StructuredRequirementVersion(
                task_id=task.id,
                version_no=1,
                status='approved',
                content_json={'modules': [{'name': 'Settlement'}]},
            )
        )
        session.add(
            TestPointVersion(
                task_id=task.id,
                version_no=1,
                status='approved',
                content_json={'points': [{'module': 'Settlement', 'name': 'Main flow'}]},
            )
        )
        session.add(
            TestCasePackageVersion(
                task_id=task.id,
                version_no=1,
                status='approved',
                content_json={'cases': [{'module': 'Settlement', 'title': 'Main flow case'}]},
            )
        )
        await session.commit()
        await session.refresh(task)

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as ac:
            yield ac, task.id

    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, tables=TEST_TABLES))
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_coverage_report(client):
    ac, task_id = client
    response = await ac.get(f'/api/tasks/{task_id}/coverage-report')

    assert response.status_code == 200
    data = response.json()
    assert data['structured_modules'] == 1
    assert data['test_points'] == 1
    assert data['generated_cases'] == 1
    assert data['coverage_ratio'] == 1.0


@pytest.mark.asyncio
async def test_publish_requires_approved_case_package(client):
    ac, task_id = client
    response = await ac.post(f'/api/tasks/{task_id}:publish')

    assert response.status_code == 200
    data = response.json()
    assert data['task_status'] == 'published'
    assert data['knowledge_asset_created'] is True
