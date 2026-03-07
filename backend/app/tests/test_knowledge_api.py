import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.knowledge_asset import KnowledgeAsset

TEST_DATABASE_URL = 'sqlite+aiosqlite:///:memory:'
TEST_TABLES = [KnowledgeAsset.__table__]


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=TEST_TABLES))

    async with async_session() as session:
        asset = KnowledgeAsset(
            asset_type='case_asset',
            title='Settlement package',
            summary='待提升为精选层',
            content_json={'cases': [{'title': 'Main flow'}]},
            status='candidate',
            quality_level='candidate',
        )
        session.add(asset)
        await session.commit()
        await session.refresh(asset)

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url='http://test') as ac:
            yield ac, asset.id

    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, tables=TEST_TABLES))
    await engine.dispose()


@pytest.mark.asyncio
async def test_promote_asset_to_curated_layer(client):
    ac, asset_id = client
    response = await ac.post(f'/api/knowledge-assets/{asset_id}:promote')

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'curated'
    assert data['quality_level'] == 'curated'
