"""add fix cost and paid status to session

Revision ID: eb676896a548
Revises: 9c1b7e4a2d11
Create Date: 2026-05-18 14:21:31.485930

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "eb676896a548"
down_revision: Union[str, Sequence[str], None] = "9c1b7e4a2d11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def upgrade() -> None:
    """Upgrade schema."""
    if not column_exists("cleaning_sessions", "fix_cost"):
        op.add_column(
            "cleaning_sessions",
            sa.Column(
                "fix_cost",
                sa.Float(),
                nullable=False,
                server_default="0",
            ),
        )


def downgrade() -> None:
    """Downgrade schema."""
    if column_exists("cleaning_sessions", "fix_cost"):
        op.drop_column("cleaning_sessions", "fix_cost")