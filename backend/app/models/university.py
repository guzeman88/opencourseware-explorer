from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.department import Department
    from app.models.roadmap import Roadmap


class University(Base):
    __tablename__ = "universities"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(500))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    country: Mapped[str | None] = mapped_column(String(100))
    youtube_channel_id: Mapped[str | None] = mapped_column(String(100))
    source_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # e.g. "mit_ocw", "yale_ocw", "stanford_see", "nptel", "berkeley"

    departments: Mapped[list[Department]] = relationship(
        "Department", back_populates="university", cascade="all, delete-orphan"
    )
    courses: Mapped[list[Course]] = relationship(
        "Course", back_populates="university", cascade="all, delete-orphan"
    )
    roadmaps: Mapped[list[Roadmap]] = relationship(
        "Roadmap", back_populates="university", cascade="all, delete-orphan"
    )
