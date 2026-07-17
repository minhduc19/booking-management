"""add user role

Revision ID: 1cec366f3691
Revises: b1a2c3d4e5f6
Create Date: 2026-07-17 16:31:06.595029

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cec366f3691'
down_revision: Union[str, Sequence[str], None] = 'b1a2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "role")
