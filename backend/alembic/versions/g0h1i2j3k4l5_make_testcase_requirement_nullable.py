"""make testcase requirement_id nullable for imported cases

Revision ID: g0h1i2j3k4l5
Revises: f9a0b1c2d3e4
Branch labels: None
Depends_on: None
"""

import sqlalchemy as sa
from alembic import op

revision = "g0h1i2j3k4l5"
down_revision = "f9a0b1c2d3e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("test_cases", "requirement_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    # Set any NULL values to a sentinel before restoring NOT NULL
    op.execute("UPDATE test_cases SET requirement_id = '00000000-0000-0000-0000-000000000000' WHERE requirement_id IS NULL")
    op.alter_column("test_cases", "requirement_id", existing_type=sa.UUID(), nullable=False)
