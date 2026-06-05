"""add course is_published flag

Revision ID: g2h3i4j5k6l7
Revises: d3e4f5a6b7c8, f1a2b3c4d5e6
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = "g2h3i4j5k6l7"
down_revision = ("d3e4f5a6b7c8", "f1a2b3c4d5e6")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column(
            "is_published",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index(
        op.f("ix_courses_is_published"),
        "courses",
        ["is_published"],
        unique=False,
    )
    op.execute(
        """
        UPDATE courses
        SET is_published = TRUE
        WHERE has_video_lectures = TRUE
           OR youtube_playlist_id IS NOT NULL
           OR total_videos > 0
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_courses_is_published"), table_name="courses")
    op.drop_column("courses", "is_published")
