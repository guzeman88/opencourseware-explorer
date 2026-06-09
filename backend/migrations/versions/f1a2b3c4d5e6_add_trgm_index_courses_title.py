"""add pg_trgm GIN index on courses.title for fast ILIKE search

Revision ID: f1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2026-05-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable the pg_trgm extension (idempotent; requires superuser or pg_trgm privilege)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # GIN index on courses.title — speeds up ILIKE '%query%' searches from O(n) to O(log n)
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_courses_title_trgm "
            "ON courses USING GIN (title gin_trgm_ops)"
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_courses_title_trgm")
