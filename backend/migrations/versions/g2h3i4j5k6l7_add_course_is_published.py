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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("courses")}
    indexes = {index["name"] for index in inspector.get_indexes("courses")}

    if "is_published" not in columns:
        op.add_column(
            "courses",
            sa.Column(
                "is_published",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
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

    if "ix_courses_is_published" not in indexes:
        op.create_index(
            op.f("ix_courses_is_published"),
            "courses",
            ["is_published"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_courses_is_published"), table_name="courses")
    op.drop_column("courses", "is_published")
