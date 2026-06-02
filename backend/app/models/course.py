from __future__ import annotations

import uuid
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.university import University
    from app.models.department import Department
    from app.models.subject import Subject
    from app.models.video import Video


class CourseLevel(str, PyEnum):
    undergraduate = "undergraduate"
    graduate = "graduate"
    professional = "professional"
    other = "other"


class Course(Base):
    __tablename__ = "courses"

    university_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Identifiers
    course_number: Mapped[str | None] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(600), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    # Classification
    level: Mapped[CourseLevel] = mapped_column(
        Enum(CourseLevel), nullable=False, default=CourseLevel.other, index=True
    )

    # Source / origin
    source_url: Mapped[str | None] = mapped_column(String(1000))
    source_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # e.g. "mit_ocw", "yale_ocw", etc.

    # Content
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    instructor: Mapped[str | None] = mapped_column(String(255))
    year: Mapped[int | None] = mapped_column(Integer)
    semester: Mapped[str | None] = mapped_column(String(30))

    # Available materials
    has_video_lectures: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_lecture_notes: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_exams: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lecture_notes_url: Mapped[str | None] = mapped_column(String(1000))
    exams_url: Mapped[str | None] = mapped_column(String(1000))

    # YouTube
    youtube_playlist_id: Mapped[str | None] = mapped_column(String(100), index=True)
    total_videos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Stats
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Full-text search column (populated via trigger / migration)
    search_vector: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # tsvector stored as text for portability

    university: Mapped[University] = orm_relationship("University", back_populates="courses")
    department: Mapped[Department | None] = orm_relationship(
        "Department", back_populates="courses"
    )
    videos: Mapped[list[Video]] = orm_relationship(
        "Video", back_populates="course", cascade="all, delete-orphan", order_by="Video.order"
    )
    course_subjects: Mapped[list[CourseSubject]] = orm_relationship(
        "CourseSubject", back_populates="course", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_courses_university_level", "university_id", "level"),
        Index("ix_courses_source_key_number", "source_key", "course_number"),
    )


class CourseSubject(Base):
    __tablename__ = "course_subjects"

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )

    course: Mapped[Course] = orm_relationship("Course", back_populates="course_subjects")
    subject: Mapped[Subject] = orm_relationship("Subject", back_populates="course_subjects")

    __table_args__ = (UniqueConstraint("course_id", "subject_id"),)


class CourseSubjectRelevance(Base):
    __tablename__ = "course_subject_relevance"

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    relationship: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="auto")
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1")

    course: Mapped[Course] = orm_relationship("Course")
    subject: Mapped[Subject] = orm_relationship("Subject")

    __table_args__ = (
        UniqueConstraint("course_id", "subject_id", name="uq_course_subject_relevance"),
        Index("ix_course_subject_relevance_subject_score", "subject_id", "score"),
        Index("ix_course_subject_relevance_course_subject", "course_id", "subject_id"),
    )
