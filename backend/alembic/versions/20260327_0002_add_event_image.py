"""add event image

Revision ID: 20260327_0002
Revises: 20260327_0001
Create Date: 2026-03-27 03:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_0002"
down_revision = "20260327_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("image_path", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "image_path")
