"""add listing_metadata table

Revision ID: e2b2d8d6df9a
Revises: 747a6abc54c1
Create Date: 2026-07-10 17:33:30.219997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'e2b2d8d6df9a'
down_revision: Union[str, Sequence[str], None] = '747a6abc54c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()

def upgrade() -> None:
    if not table_exists("listing_metadata"):
        op.create_table(
            "listing_metadata",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("listing", sa.String(), nullable=False),
            sa.Column("listing_number", sa.String(), nullable=True),
            sa.Column("property_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("listing"),
        )
        op.create_index(op.f("ix_listing_metadata_id"), "listing_metadata", ["id"], unique=False)
        op.create_index(op.f("ix_listing_metadata_listing"), "listing_metadata", ["listing"], unique=True)


def downgrade() -> None:
    if table_exists("listing_metadata"):
        op.drop_index(op.f("ix_listing_metadata_listing"), table_name="listing_metadata")
        op.drop_index(op.f("ix_listing_metadata_id"), table_name="listing_metadata")
        op.drop_table("listing_metadata")