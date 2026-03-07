#!/usr/bin/env python3
"""
数据库初始化脚本
启用 pgvector 扩展并创建所有数据库表
"""
import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.database import engine
from app.models import Base

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def init_db() -> None:
    """初始化数据库表"""
    try:
        async with engine.begin() as conn:
            # 启用 pgvector 扩展
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("✅ pgvector 扩展已启用")
            except SQLAlchemyError as e:
                logger.error(f"❌ 启用 pgvector 扩展失败: {e}")
                raise

            # 创建所有表
            try:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ 数据库表创建成功")
            except SQLAlchemyError as e:
                logger.error(f"❌ 创建表失败: {e}")
                raise

        logger.info("✅ 数据库初始化完成")

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_db())
