"""add uploaded pdfs

Revision ID: c5e3b3b02d8f
Revises: 1cec366f3691
Create Date: 2026-09-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c5e3b3b02d8f"
down_revision = "1cec366f3691"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "uploaded_pdfs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("storage_name", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_name"),
    )
    op.create_index(op.f("ix_uploaded_pdfs_id"), "uploaded_pdfs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_uploaded_pdfs_id"), table_name="uploaded_pdfs")
    op.drop_table("uploaded_pdfs")
