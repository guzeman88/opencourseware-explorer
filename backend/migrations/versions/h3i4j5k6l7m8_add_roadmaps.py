"""add roadmaps

Revision ID: h3i4j5k6l7m8
Revises: g2h3i4j5k6l7
Create Date: 2026-06-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h3i4j5k6l7m8"
down_revision: Union[str, None] = "g2h3i4j5k6l7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roadmaps",
        sa.Column("university_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=300), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("degree_type", sa.String(length=100), nullable=True),
        sa.Column("major", sa.String(length=255), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("estimated_years", sa.Integer(), nullable=True),
        sa.Column("website_url", sa.String(length=1000), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["university_id"], ["universities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmaps_university_id", "roadmaps", ["university_id"])
    op.create_index("ix_roadmaps_slug", "roadmaps", ["slug"], unique=True)

    op.create_table(
        "roadmap_entries",
        sa.Column("roadmap_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("course_number", sa.String(length=100), nullable=True),
        sa.Column("course_title", sa.String(length=500), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("semester", sa.String(length=50), nullable=True),
        sa.Column("year_in_program", sa.Integer(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("units", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("subject_slug", sa.String(length=200), nullable=True),
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
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["roadmap_id"], ["roadmaps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmap_entries_course_id", "roadmap_entries", ["course_id"])
    op.create_index("ix_roadmap_entries_roadmap_id", "roadmap_entries", ["roadmap_id"])


def downgrade() -> None:
    op.drop_index("ix_roadmap_entries_roadmap_id", table_name="roadmap_entries")
    op.drop_index("ix_roadmap_entries_course_id", table_name="roadmap_entries")
    op.drop_table("roadmap_entries")
    op.drop_index("ix_roadmaps_slug", table_name="roadmaps")
    op.drop_index("ix_roadmaps_university_id", table_name="roadmaps")
    op.drop_table("roadmaps")
