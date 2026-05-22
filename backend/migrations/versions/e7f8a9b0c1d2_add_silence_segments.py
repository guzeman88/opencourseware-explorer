"""add silence_segments to videos

Revision ID: e7f8a9b0c1d2
Revises: c1a2b3d4e5f6
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "videos",
        sa.Column("silence_segments", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("videos", "silence_segments")
