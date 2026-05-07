"""add user library

Revision ID: c1a2b3d4e5f6
Revises: abb770ac77cb
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, None] = "abb770ac77cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_library_courses",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "course_id", name="uq_user_library_course"),
    )
    op.create_index(
        "ix_user_library_courses_user_id", "user_library_courses", ["user_id"]
    )
    op.create_index(
        "ix_user_library_courses_course_id", "user_library_courses", ["course_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_user_library_courses_course_id", "user_library_courses")
    op.drop_index("ix_user_library_courses_user_id", "user_library_courses")
    op.drop_table("user_library_courses")
