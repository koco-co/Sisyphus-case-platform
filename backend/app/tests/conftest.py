import pytest
import pytest_asyncio
from sqlalchemy import JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.database import Base, get_db
from app.main import app


# 使用 SQLite 内存数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    # 为 SQLite 替换 JSONB 类型为 JSON
    from sqlalchemy.dialects.postgresql import JSONB
    from app.models.requirement import Requirement
    from app.models.test_case_new import TestCaseNew

    # 临时替换类型
    original_types = {}
    for table in [Requirement, TestCaseNew]:
        for column in table.__table__.columns:
            if isinstance(column.type, JSONB):
                original_types[column] = column.type
                column.type = JSON()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # 恢复原始类型
    for column, original_type in original_types.items():
        column.type = original_type


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
