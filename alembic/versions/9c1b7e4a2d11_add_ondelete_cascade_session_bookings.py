"""Add ON DELETE CASCADE to session_bookings.session_id FK

Revision ID: 9c1b7e4a2d11
Revises: eb676896a548
Create Date: 2026-05-20 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c1b7e4a2d11"
down_revision: Union[str, Sequence[str], None] = "ddfbfd3c8356"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()
    if "session_bookings" not in table_names:
        return

    op.create_table(
        "session_bookings_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("confirmation_code", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["confirmation_code"],
            ["bookings.confirmation_code"],
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["cleaning_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO session_bookings_new (id, session_id, confirmation_code)
            SELECT id, session_id, confirmation_code
            FROM session_bookings
            """
        )
    )

    op.drop_table("session_bookings")
    op.rename_table("session_bookings_new", "session_bookings")
    op.create_index(op.f("ix_session_bookings_id"), "session_bookings", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()
    if "session_bookings" not in table_names:
        return

    op.create_table(
        "session_bookings_old",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("confirmation_code", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["confirmation_code"],
            ["bookings.confirmation_code"],
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["cleaning_sessions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO session_bookings_old (id, session_id, confirmation_code)
            SELECT id, session_id, confirmation_code
            FROM session_bookings
            """
        )
    )

    op.drop_index(op.f("ix_session_bookings_id"), table_name="session_bookings")
    op.drop_table("session_bookings")
    op.rename_table("session_bookings_old", "session_bookings")
    op.create_index(op.f("ix_session_bookings_id"), "session_bookings", ["id"], unique=False)
