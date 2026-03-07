import os
import tempfile

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
        project = Project(name='测试项目', description='任务接口测试')
        session.add(project)
        await session.commit()
        await session.refresh(project)

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as ac:
            yield ac, project

    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, tables=TEST_TABLES))
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_requirement_task(client):
    ac, project = client
    response = await ac.post(
        '/api/tasks',
        json={
            'title': 'Settlement rules',
            'project_id': project.id,
            'source_type': 'pdf',
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Settlement rules'
    assert data['project_id'] == project.id
    assert data['current_stage'] == 'intake'
    assert data['task_status'] == 'created'


@pytest.mark.asyncio
async def test_upload_task_document(client):
    ac, project = client
    task_response = await ac.post(
        '/api/tasks',
        json={
            'title': 'Markdown requirement',
            'project_id': project.id,
            'source_type': 'md',
        },
    )
    task_id = task_response.json()['id']

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write('# Requirement\n\nTask intake content.')
        temp_path = f.name

    try:
        with open(temp_path, 'rb') as uploaded:
            response = await ac.post(
                f'/api/tasks/{task_id}/documents',
                files={'file': ('requirement.md', uploaded, 'text/markdown')},
            )

        assert response.status_code == 201
        data = response.json()
        assert data['task_id'] == task_id
        assert data['file_name'] == 'requirement.md'
        assert 'Requirement' in data['extracted_text']
    finally:
        os.unlink(temp_path)
