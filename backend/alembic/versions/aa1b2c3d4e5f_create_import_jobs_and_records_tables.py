"""create import_jobs and import_records tables

Revision ID: aa1b2c3d4e5f
Revises: ee8a72884ae2
Create Date: 2026-03-11 14:00:00.000000

"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "aa1b2c3d4e5f"
down_revision = "ee8a72884ae2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("total_records", sa.Integer, nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duplicate_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("health_report", postgresql.JSONB, nullable=True),
        sa.Column("field_mapping", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_import_jobs_status", "import_jobs", ["status"])
    op.create_index("ix_import_jobs_deleted_at", "import_jobs", ["deleted_at"])

    op.create_table(
        "import_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_jobs.id"), nullable=False),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("original_title", sa.String(500), nullable=True),
        sa.Column("mapped_title", sa.String(500), nullable=True),
        sa.Column("raw_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("mapped_data", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("match_score", sa.Float, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("duplicate_of", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_import_records_job_id", "import_records", ["job_id"])
    op.create_index("ix_import_records_status", "import_records", ["status"])


def downgrade() -> None:
    op.drop_table("import_records")
    op.drop_table("import_jobs")
