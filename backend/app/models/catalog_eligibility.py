from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CourseCatalogEligibility(Base):
    __tablename__ = "course_catalog_eligibility"

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reasons: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    actual_video_count: Mapped[int] = mapped_column(Integer, nullable=False)
    current_catalog_ready: Mapped[bool] = mapped_column(Boolean, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        Index("ix_course_catalog_eligibility_status_policy", "status", "policy_version"),
    )


class SubjectCatalogCount(Base):
    __tablename__ = "subject_catalog_counts"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    course_count: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
