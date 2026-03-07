import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import app.models.test_point_version as test_point_version_model

from app.database import Base, get_db
from app.main import app
from app.models.project import Project
from app.models.requirement_task import RequirementTask
from app.models.structured_requirement_version import StructuredRequirementVersion

TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'
TEST_TABLES = [
    Project.__table__,
    RequirementTask.__table__,
    StructuredRequirementVersion.__table__,
    test_point_version_model.TestPointVersion.__table__,
]


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=TEST_TABLES))

    async with async_session() as session:
        project = Project(name='测试点项目', description='测试点生成')
        session.add(project)
        await session.flush()

        task = RequirementTask(
            project_id=project.id,
            title='Point me',
            source_type='md',
            current_stage='test_point_design',
            task_status='structured_ready',
        )
        session.add(task)
        await session.flush()

        session.add(
            StructuredRequirementVersion(
                task_id=task.id,
                version_no=1,
                status='approved',
                content_json={
                    'modules': [
                        {
                            'name': 'Settlement',
                            'summary': 'Validate period close and posting rules.',
                        }
                    ]
                },
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
async def test_generate_test_point_version(client):
    ac, task_id = client

    response = await ac.post(f'/api/tasks/{task_id}/test-point-versions:generate')

    assert response.status_code == 202
    data = response.json()
    assert data['task_id'] == task_id
    assert data['version_no'] == 1
    assert data['status'] == 'draft'
    assert data['content_json']['points'][0]['module'] == 'Settlement'
