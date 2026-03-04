"""添加 embedding 列到 test_cases 表"""


async def upgrade():
    """添加 embedding 列"""
    from app.database import engine

    async with engine.begin() as conn:
        await conn.execute(
            """
            ALTER TABLE test_cases
            ADD COLUMN IF NOT EXISTS embedding jsonb
        """
        )


async def downgrade():
    """移除 embedding 列"""
    from app.database import engine

    async with engine.begin() as conn:
        await conn.execute(
            """
            ALTER TABLE test_cases
            DROP COLUMN IF EXISTS embedding
        """
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(upgrade())
    print("✅ Migration completed")
