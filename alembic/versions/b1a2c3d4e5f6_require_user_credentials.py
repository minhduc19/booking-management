"""Require user email and password hash.

Revision ID: b1a2c3d4e5f6
Revises: 4188ea0fbb20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4188ea0fbb20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("email", existing_type=sa.String(), nullable=False)
        batch_op.alter_column("hashed_password", existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("hashed_password", existing_type=sa.String(), nullable=True)
        batch_op.alter_column("email", existing_type=sa.String(), nullable=True)
