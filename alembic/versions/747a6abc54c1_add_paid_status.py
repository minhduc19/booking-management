"""add paid status

Revision ID: 747a6abc54c1
Revises: eb676896a548
Create Date: 2026-06-01 14:21:05.109488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "747a6abc54c1"
down_revision: Union[str, Sequence[str], None] = "eb676896a548"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def upgrade() -> None:
    """Upgrade schema."""
    if not column_exists("cleaning_sessions", "paid_status"):
        op.add_column(
            "cleaning_sessions",
            sa.Column(
                "paid_status",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade() -> None:
    """Downgrade schema."""
    if column_exists("cleaning_sessions", "paid_status"):
        op.drop_column("cleaning_sessions", "paid_status")