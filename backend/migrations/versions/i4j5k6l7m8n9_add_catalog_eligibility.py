"""add catalog eligibility sidecar

Revision ID: i4j5k6l7m8n9
Revises: h3i4j5k6l7m8
Create Date: 2026-06-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "i4j5k6l7m8n9"
down_revision: Union[str, None] = "h3i4j5k6l7m8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_catalog_eligibility",
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("actual_video_count", sa.Integer(), nullable=False),
        sa.Column("current_catalog_ready", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.String(length=50), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id"),
    )
    op.create_index(
        "ix_course_catalog_eligibility_course_id",
        "course_catalog_eligibility",
        ["course_id"],
    )
    op.create_index(
        "ix_course_catalog_eligibility_status",
        "course_catalog_eligibility",
        ["status"],
    )
    op.create_index(
        "ix_course_catalog_eligibility_status_policy",
        "course_catalog_eligibility",
        ["status", "policy_version"],
    )
    op.create_table(
        "subject_catalog_counts",
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("course_count", sa.Integer(), nullable=False),
        sa.Column("policy_version", sa.String(length=50), nullable=False),
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
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_id"),
    )
    op.create_index(
        "ix_subject_catalog_counts_subject_id",
        "subject_catalog_counts",
        ["subject_id"],
    )
    op.create_index(
        "ix_subject_catalog_counts_policy_version",
        "subject_catalog_counts",
        ["policy_version"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_subject_catalog_counts_policy_version",
        table_name="subject_catalog_counts",
    )
    op.drop_index(
        "ix_subject_catalog_counts_subject_id",
        table_name="subject_catalog_counts",
    )
    op.drop_table("subject_catalog_counts")
    op.drop_index(
        "ix_course_catalog_eligibility_status_policy",
        table_name="course_catalog_eligibility",
    )
    op.drop_index(
        "ix_course_catalog_eligibility_status",
        table_name="course_catalog_eligibility",
    )
    op.drop_index(
        "ix_course_catalog_eligibility_course_id",
        table_name="course_catalog_eligibility",
    )
    op.drop_table("course_catalog_eligibility")
