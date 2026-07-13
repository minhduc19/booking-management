"""add archive_status to booking

Revision ID: 6eb47f75272e
Revises: e2b2d8d6df9a
Create Date: 2026-07-13 10:34:42.844253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6eb47f75272e'
down_revision: Union[str, Sequence[str], None] = 'e2b2d8d6df9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("bookings", sa.Column("archive_status", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("bookings", "archive_status")
