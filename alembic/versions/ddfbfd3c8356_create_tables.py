"""Create tables

Revision ID: ddfbfd3c8356
Revises: 
Create Date: 2026-05-15 19:16:43.297991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddfbfd3c8356'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "properties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("address"),
    )
    op.create_index(op.f("ix_properties_id"), "properties", ["id"], unique=False)

    op.create_table(
        "cleaners",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("rate", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_cleaners_id"), "cleaners", ["id"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("confirmation_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("guest_name", sa.String(), nullable=False),
        sa.Column("contact", sa.String(), nullable=True),
        sa.Column("adults", sa.Integer(), nullable=True),
        sa.Column("children", sa.Integer(), nullable=True),
        sa.Column("infants", sa.Integer(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("nights", sa.Integer(), nullable=False),
        sa.Column("booked_date", sa.Date(), nullable=True),
        sa.Column("listing", sa.String(), nullable=True),
        sa.Column("listing_number", sa.String(), nullable=True),
        sa.Column("earnings", sa.String(), nullable=True),
        sa.Column("property_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookings_confirmation_code"), "bookings", ["confirmation_code"], unique=True)
    op.create_index(op.f("ix_bookings_id"), "bookings", ["id"], unique=False)

    op.create_table(
        "cleaning_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cleaner_id", sa.Integer(), nullable=False),
        sa.Column("clean_date", sa.Date(), nullable=False),
        sa.Column("hours", sa.Integer(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["cleaner_id"], ["cleaners.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cleaning_sessions_id"), "cleaning_sessions", ["id"], unique=False)

    op.create_table(
        "session_bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("confirmation_code", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["confirmation_code"], ["bookings.confirmation_code"]),
        sa.ForeignKeyConstraint(["session_id"], ["cleaning_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_session_bookings_id"), "session_bookings", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_session_bookings_id"), table_name="session_bookings")
    op.drop_table("session_bookings")

    op.drop_index(op.f("ix_cleaning_sessions_id"), table_name="cleaning_sessions")
    op.drop_table("cleaning_sessions")

    op.drop_index(op.f("ix_bookings_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_confirmation_code"), table_name="bookings")
    op.drop_table("bookings")

    op.drop_index(op.f("ix_cleaners_id"), table_name="cleaners")
    op.drop_table("cleaners")

    op.drop_index(op.f("ix_properties_id"), table_name="properties")
    op.drop_table("properties")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
