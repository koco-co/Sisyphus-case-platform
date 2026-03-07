import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.project import Project
from app.models.requirement_task import RequirementTask
from app.models.source_document import SourceDocument

TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'
TEST_TABLES = [
    Project.__table__,
    RequirementTask.__table__,
    SourceDocument.__table__,
]


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=TEST_TABLES))

    async with async_session() as session:
        project = Project(name='预处理项目', description='ingestion 测试')
        session.add(project)
        await session.flush()

        task = RequirementTask(
            project_id=project.id,
            title='待结构化任务',
            source_type='md',
            current_stage='intake',
            task_status='created',
        )
        session.add(task)
        await session.flush()

        session.add(
            SourceDocument(
                task_id=task.id,
                file_name='req.md',
                file_type='text/markdown',
                storage_path='/tmp/req.md',
                extracted_text='# Requirement\n\nNeed structured parsing.',
                quality_score=0.9,
            )
        )
        await session.commit()

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
async def test_run_ingestion_job_marks_task_ready(client):
    ac, task_id = client

    response = await ac.post(f'/api/tasks/{task_id}/ingestion:run')

    assert response.status_code == 202
    data = response.json()
    assert data['task_id'] == task_id
    assert data['task_status'] == 'ready_for_structuring'
    assert data['current_stage'] == 'structuring'
    assert 'Requirement' in data['input_summary']
