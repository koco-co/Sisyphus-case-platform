"""add uda and ai config tables

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-11 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- M01: parsed_documents (UDA 文档解析) ---
    op.create_table(
        "parsed_documents",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "requirement_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requirements.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("file_size", sa.Integer, default=0, nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=True),
        sa.Column("content_text", sa.Text, nullable=True),
        sa.Column("content_ast", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "parse_status", sa.String(20), server_default="pending", nullable=False
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- AI Configurations (Prompt / 模型配置) ---
    op.create_table(
        "ai_configurations",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "scope", sa.String(20), server_default="global", nullable=False
        ),
        sa.Column(
            "scope_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "system_rules_version",
            sa.String(20),
            server_default="1.0",
            nullable=False,
        ),
        sa.Column("team_standard_prompt", sa.Text, nullable=True),
        sa.Column("module_rules", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "output_preference", sa.dialects.postgresql.JSONB, nullable=True
        ),
        sa.Column(
            "scope_preference", sa.dialects.postgresql.JSONB, nullable=True
        ),
        sa.Column("rag_config", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "custom_checklist", sa.dialects.postgresql.JSONB, nullable=True
        ),
        sa.Column("llm_model", sa.String(50), nullable=True),
        sa.Column("llm_temperature", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ai_configurations")
    op.drop_table("parsed_documents")
