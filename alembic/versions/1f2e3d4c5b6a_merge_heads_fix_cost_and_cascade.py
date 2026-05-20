"""Merge heads: fix_cost migration and cascade FK migration

Revision ID: 1f2e3d4c5b6a
Revises: eb676896a548, 9c1b7e4a2d11
Create Date: 2026-05-20 00:00:01.000000
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "1f2e3d4c5b6a"
down_revision: Union[str, Sequence[str], None] = ("eb676896a548", "9c1b7e4a2d11")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
