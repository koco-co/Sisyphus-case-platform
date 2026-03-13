"""merge_all_heads

Revision ID: ec4b13b4028c
Revises: b3c4d5e6f7a8, aa1b2c3d4e5f, g0h1i2j3k4l5
Create Date: 2026-03-14 03:40:07.346495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec4b13b4028c'
down_revision: Union[str, Sequence[str], None] = ('b3c4d5e6f7a8', 'aa1b2c3d4e5f', 'g0h1i2j3k4l5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
