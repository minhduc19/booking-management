"""new metadata column in booking for listing number

Revision ID: 4188ea0fbb20
Revises: 6eb47f75272e
Create Date: 2026-07-15 12:03:05.920151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '4188ea0fbb20'
down_revision: Union[str, Sequence[str], None] = '6eb47f75272e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return column_name in [column["name"] for column in inspector.get_columns(table_name)]


def upgrade() -> None:
    """Upgrade schema."""
    if not column_exists("bookings", "listing_metadata_id"):
        with op.batch_alter_table("bookings") as batch_op:
            batch_op.add_column(sa.Column("listing_metadata_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_bookings_listing_metadata_id_listing_metadata",
                "listing_metadata",
                ["listing_metadata_id"],
                ["id"],
            )


def downgrade() -> None:
    """Downgrade schema."""
    if column_exists("bookings", "listing_metadata_id"):
        with op.batch_alter_table("bookings") as batch_op:
            batch_op.drop_constraint(
                "fk_bookings_listing_metadata_id_listing_metadata",
                type_="foreignkey",
            )
            batch_op.drop_column("listing_metadata_id")
