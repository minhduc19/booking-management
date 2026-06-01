"""add paid status

Revision ID: 747a6abc54c1
Revises: 9c1b7e4a2d11
Create Date: 2026-06-01 14:21:05.109488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '747a6abc54c1'
down_revision: Union[str, Sequence[str], None] = '9c1b7e4a2d11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "cleaning_sessions",
        sa.Column("paid_status", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("cleaning_sessions", "paid_status")
