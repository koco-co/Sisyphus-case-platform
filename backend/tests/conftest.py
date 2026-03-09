"""公共 Fixture — 异步测试基础设施"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_async_session
from app.main import app

# 使用 SQLite 异步引擎做单元测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_test = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """提供独立的异步数据库会话（每次测试自动回滚）。"""
    async with async_session_test() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """提供异步 HTTP 测试客户端。"""

    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_test() as session:
            yield session

    app.dependency_overrides[get_async_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def mock_llm() -> AsyncMock:
    """Mock LLM 客户端，用于单元测试 AI 引擎。"""
    mock = AsyncMock()
    mock.ainvoke.return_value.content = '{"result": "mocked"}'
    return mock
