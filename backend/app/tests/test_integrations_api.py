import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.project import Project
from app.models.requirement_task import RequirementTask
from app.models.test_case_package_version import TestCasePackageVersion
from app.models.integration_sync_record import IntegrationSyncRecord

TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'
TEST_TABLES = [
    Project.__table__,
    RequirementTask.__table__,
    TestCasePackageVersion.__table__,
    IntegrationSyncRecord.__table__,
]


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=TEST_TABLES))

    async with async_session() as session:
        project = Project(name='集成项目', description='导出与同步')
        session.add(project)
        await session.flush()

        task = RequirementTask(
            project_id=project.id,
            title='Sync me',
            source_type='md',
            current_stage='published',
            task_status='published',
        )
        session.add(task)
        await session.flush()

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
async def test_export_markdown_package(client):
    ac, task_id = client
    response = await ac.post(f'/api/tasks/{task_id}:sync', json={'provider': 'markdown'})

    assert response.status_code == 202
    data = response.json()
    assert data['provider'] == 'markdown'
    assert data['status'] == 'completed'
    assert data['output_path'].endswith('.md')
