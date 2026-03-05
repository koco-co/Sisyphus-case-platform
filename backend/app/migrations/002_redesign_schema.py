"""重构数据库架构 - 添加新表支持前端重构

创建以下表：
- files: 文件存储管理
- requirements: 结构化需求（关联 projects）
- test_cases_new: 新测试用例结构
- export_templates: 导出模板配置
- conversations: 对话历史
- llm_configs: LLM 配置（独立于 user_configs）
"""

from sqlalchemy import text


async def upgrade():
    """添加新表"""
    from app.database import engine

    async with engine.begin() as conn:
        # 1. 文件表
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    filename VARCHAR(255) NOT NULL,
                    original_name VARCHAR(255) NOT NULL,
                    mime_type VARCHAR(100),
                    size BIGINT,
                    storage_type VARCHAR(20) DEFAULT 'local',
                    storage_path VARCHAR(500),
                    parsed_content TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
        )

        # 2. 需求表（project_id 使用 INTEGER 匹配 projects 表）
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS requirements (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    content JSONB DEFAULT '{}',
                    source_file_id UUID REFERENCES files(id),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
        )

        # 3. 新测试用例表
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS test_cases_new (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    requirement_id UUID NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
                    title VARCHAR(500) NOT NULL,
                    priority VARCHAR(10) DEFAULT 'P2',
                    preconditions TEXT,
                    steps JSONB DEFAULT '[]',
                    tags TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
        )

        # 4. 导出模板表
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS export_templates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    field_config JSONB DEFAULT '{}',
                    format_config JSONB DEFAULT '{}',
                    filter_config JSONB DEFAULT '{}',
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
        )

        # 5. 对话历史表
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    requirement_id UUID REFERENCES requirements(id) ON DELETE CASCADE,
                    messages JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
        )

        # 6. LLM 配置表（新表，不影响现有 user_configs）
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS llm_configs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    provider VARCHAR(50) DEFAULT 'openai',
                    api_key_encrypted VARCHAR(500),
                    model VARCHAR(100) DEFAULT 'gpt-4',
                    config_json JSONB DEFAULT '{}',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
        )

        # 创建索引
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_requirements_project_id ON requirements(project_id)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_test_cases_new_requirement_id ON test_cases_new(requirement_id)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_conversations_requirement_id ON conversations(requirement_id)")
        )


async def downgrade():
    """移除新表"""
    from app.database import engine

    async with engine.begin() as conn:
        # 删除索引
        await conn.execute(text("DROP INDEX IF EXISTS idx_conversations_requirement_id"))
        await conn.execute(text("DROP INDEX IF EXISTS idx_test_cases_new_requirement_id"))
        await conn.execute(text("DROP INDEX IF EXISTS idx_requirements_project_id"))

        # 删除表（按依赖顺序）
        await conn.execute(text("DROP TABLE IF EXISTS llm_configs"))
        await conn.execute(text("DROP TABLE IF EXISTS conversations"))
        await conn.execute(text("DROP TABLE IF EXISTS export_templates"))
        await conn.execute(text("DROP TABLE IF EXISTS test_cases_new"))
        await conn.execute(text("DROP TABLE IF EXISTS requirements"))
        await conn.execute(text("DROP TABLE IF EXISTS files"))


if __name__ == "__main__":
    import asyncio

    asyncio.run(upgrade())
    print("✅ Migration 002_redesign_schema completed")
