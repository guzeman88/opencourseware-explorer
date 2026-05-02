from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.university import University
    from app.models.course import Course


class Roadmap(Base):
    __tablename__ = "roadmaps"

    university_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(300), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    degree_type: Mapped[str | None] = mapped_column(String(100))   # "Bachelor of Science"
    major: Mapped[str | None] = mapped_column(String(255))         # "Computer Science"
    department: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    estimated_years: Mapped[int | None] = mapped_column(Integer)
    website_url: Mapped[str | None] = mapped_column(String(1000))

    university: Mapped["University"] = relationship("University", back_populates="roadmaps", lazy="select")
    entries: Mapped[list["RoadmapEntry"]] = relationship(
        "RoadmapEntry", back_populates="roadmap", order_by="RoadmapEntry.position", cascade="all, delete-orphan"
    )


class RoadmapEntry(Base):
    __tablename__ = "roadmap_entries"

    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    course_number: Mapped[str | None] = mapped_column(String(100))   # "18.01SC"
    course_title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))        # "Core", "Math", "Elective"
    semester: Mapped[str | None] = mapped_column(String(50))         # "Fall Year 1"
    year_in_program: Mapped[int | None] = mapped_column(Integer)     # 1–4
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    units: Mapped[int | None] = mapped_column(Integer)               # credit hours / units
    notes: Mapped[str | None] = mapped_column(String(500))
    subject_slug: Mapped[str | None] = mapped_column(String(200), nullable=True)

    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="entries")
    course: Mapped["Course | None"] = relationship("Course", lazy="select")
