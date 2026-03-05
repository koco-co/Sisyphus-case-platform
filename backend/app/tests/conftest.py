import asyncio
import os
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

from app.database import Base, get_db
from app.main import app


# 使用测试数据库 (PostgreSQL)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://sisyphus:sisyphus123@localhost:5433/sisyphus_test"
)

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """创建会话级别的事件循环"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session(event_loop) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    # 清理所有表数据
    async with test_engine.begin() as conn:
        # 按依赖顺序删除数据
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_client_with_db(db_session: AsyncSession):
    """创建带有测试数据库的测试客户端"""
    from httpx import ASGITransport, AsyncClient

    # Override get_db 依赖
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
