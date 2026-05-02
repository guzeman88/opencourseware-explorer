from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.course import CourseSubject


class Subject(Base):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True
    )

    parent: Mapped[Subject | None] = relationship(
        "Subject", remote_side="Subject.id", back_populates="children"
    )
    children: Mapped[list[Subject]] = relationship("Subject", back_populates="parent")
    course_subjects: Mapped[list[CourseSubject]] = relationship(
        "CourseSubject", back_populates="subject"
    )
