"""添加 embedding 列到 test_cases 表"""

from sqlalchemy import text


async def upgrade():
    """添加 embedding 列"""
    from app.database import engine

    async with engine.begin() as conn:
        # 启用 pgvector 扩展
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # 先删除旧的 embedding 列（如果存在且类型不是 VECTOR）
        await conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'test_cases' AND column_name = 'embedding'
                        AND data_type != 'vector'
                    ) THEN
                        ALTER TABLE test_cases DROP COLUMN embedding;
                    END IF;
                END $$;
            """
            )
        )

        # 添加 VECTOR 列
        await conn.execute(
            text(
                """
                ALTER TABLE test_cases
                ADD COLUMN IF NOT EXISTS embedding VECTOR(384)
            """
            )
        )


async def downgrade():
    """移除 embedding 列"""
    from app.database import engine

    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                ALTER TABLE test_cases
                DROP COLUMN IF EXISTS embedding
            """
            )
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(upgrade())
    print("✅ Migration completed")
