"""new metadata column in booking for listing number

Revision ID: 4188ea0fbb20
Revises: 6eb47f75272e
Create Date: 2026-07-15 12:03:05.920151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4188ea0fbb20'
down_revision: Union[str, Sequence[str], None] = '6eb47f75272e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
