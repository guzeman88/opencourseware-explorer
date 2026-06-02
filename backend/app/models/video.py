from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.course import Course


class Video(Base):
    __tablename__ = "videos"

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    youtube_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    view_count: Mapped[int | None] = mapped_column(BigInteger)
    silence_segments: Mapped[list | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=True
    )

    course: Mapped[Course] = relationship("Course", back_populates="videos")

    @property
    def youtube_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.youtube_id}"

    @property
    def embed_url(self) -> str:
        return f"https://www.youtube.com/embed/{self.youtube_id}"
