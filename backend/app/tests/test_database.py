import pytest
from sqlalchemy import text
from app.database import get_db


@pytest.mark.asyncio
async def test_database_connection():
    """测试数据库连接是否正常"""
    async for db in get_db():
        result = await db.execute(text("SELECT 1"))
        assert result.scalar() == 1
        break
