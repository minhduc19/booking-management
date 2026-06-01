"""add fix cost and paid status to session

Revision ID: eb676896a548
Revises: ddfbfd3c8356
Create Date: 2026-05-18 14:21:31.485930

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb676896a548'
down_revision: Union[str, Sequence[str], None] = '9c1b7e4a2d11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "cleaning_sessions",
        sa.Column("fix_cost", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("cleaning_sessions", "fix_cost")
