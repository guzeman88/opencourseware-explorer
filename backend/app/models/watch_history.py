from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserWatchHistory(Base):
    """Tracks the last video a user watched in each course."""

    __tablename__ = "user_watch_history"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_watch_history"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
