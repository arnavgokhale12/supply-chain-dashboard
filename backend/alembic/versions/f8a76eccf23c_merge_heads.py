"""merge heads

Revision ID: f8a76eccf23c
Revises: 0897940a6520, 9fcb0c4c6771
Create Date: 2026-01-05 19:35:14.794156

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a76eccf23c'
down_revision: Union[str, Sequence[str], None] = ('0897940a6520', '9fcb0c4c6771')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
