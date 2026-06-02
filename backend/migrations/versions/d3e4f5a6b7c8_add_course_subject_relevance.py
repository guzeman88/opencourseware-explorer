"""add course subject relevance

Revision ID: d3e4f5a6b7c8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_subject_relevance",
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("relationship", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="auto"),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="v1"),
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
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "subject_id", name="uq_course_subject_relevance"),
    )
    op.create_index(
        "ix_course_subject_relevance_subject_score",
        "course_subject_relevance",
        ["subject_id", "score"],
    )
    op.create_index(
        "ix_course_subject_relevance_course_subject",
        "course_subject_relevance",
        ["course_id", "subject_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_course_subject_relevance_course_subject",
        table_name="course_subject_relevance",
    )
    op.drop_index(
        "ix_course_subject_relevance_subject_score",
        table_name="course_subject_relevance",
    )
    op.drop_table("course_subject_relevance")
