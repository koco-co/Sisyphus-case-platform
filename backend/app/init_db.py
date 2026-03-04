#!/usr/bin/env python3
"""
数据库初始化脚本
启用 pgvector 扩展并创建所有数据库表
"""
import asyncio
from app.database import engine
from app.models import Base


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        # 启用 pgvector 扩展
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 数据库初始化完成")


if __name__ == "__main__":
    asyncio.run(init_db())
