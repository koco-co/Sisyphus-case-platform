# backend/app/migrations/versions/001_redesign_schema.py
"""redesign schema

Revision ID: 001_redesign
Revises:
Create Date: 2026-03-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_redesign'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 文件表
    op.create_table(
        'files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_name', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('size', sa.BigInteger),
        sa.Column('storage_type', sa.String(20), server_default='local'),
        sa.Column('storage_path', sa.String(500)),
        sa.Column('parsed_content', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 需求表
    op.create_table(
        'requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', postgresql.JSONB, server_default='{}'),
        sa.Column('source_file_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('files.id')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 测试用例表（重构）
    op.create_table(
        'test_cases_new',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requirements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('priority', sa.String(10), server_default='P2'),
        sa.Column('preconditions', sa.Text),
        sa.Column('steps', postgresql.JSONB, server_default='[]'),
        sa.Column('tags', postgresql.ARRAY(sa.Text), server_default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 导出模板表
    op.create_table(
        'export_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('field_config', postgresql.JSONB, server_default='{}'),
        sa.Column('format_config', postgresql.JSONB, server_default='{}'),
        sa.Column('filter_config', postgresql.JSONB, server_default='{}'),
        sa.Column('is_default', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 对话历史表
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requirements.id', ondelete='CASCADE')),
        sa.Column('messages', postgresql.JSONB, server_default='[]'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # 用户配置表
    op.create_table(
        'user_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('llm_config', postgresql.JSONB, server_default='{}'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('user_configs')
    op.drop_table('conversations')
    op.drop_table('export_templates')
    op.drop_table('test_cases_new')
    op.drop_table('requirements')
    op.drop_table('files')
