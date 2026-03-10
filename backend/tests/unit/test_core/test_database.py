"""数据库连接管理回归测试。"""

from __future__ import annotations

from sqlalchemy.pool import NullPool

import app.core.database as database


class TestGetEngine:
    async def test_get_engine_uses_null_pool_during_pytest(self):
        """pytest 多事件循环场景下应避免复用连接池中的连接。"""
        database.get_session_factory.cache_clear()
        database.get_engine.cache_clear()

        engine = database.get_engine()

        try:
            assert isinstance(engine.sync_engine.pool, NullPool)
        finally:
            await engine.dispose()
            database.get_session_factory.cache_clear()
            database.get_engine.cache_clear()
