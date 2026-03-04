#!/usr/bin/env python3
"""
数据库初始化脚本
创建所有表
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.models import Base
from app.config import settings


async def init_db():
    """初始化数据库表"""
    engine = create_async_engine(settings.database_url, echo=True)

    async with engine.begin() as conn:
        # 删除所有表（谨慎使用）
        await conn.run_sync(Base.metadata.drop_all)

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("数据库初始化完成!")


if __name__ == "__main__":
    asyncio.run(init_db())
