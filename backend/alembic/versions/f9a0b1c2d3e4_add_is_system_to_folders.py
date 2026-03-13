"""add is_system to test_case_folders

Revision ID: f9a0b1c2d3e4
Revises: ee8a72884ae2
Branch_labels: None
Depends_on: None
"""

from alembic import op
import sqlalchemy as sa

revision = "f9a0b1c2d3e4"
down_revision = "ee8a72884ae2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_case_folders",
        sa.Column("is_system", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("test_case_folders", "is_system")
