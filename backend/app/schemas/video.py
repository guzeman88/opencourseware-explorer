from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from app.schemas.base import OCWBase, TimestampMixin


class VideoBase(OCWBase):
    youtube_id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    order: int = 0
    published_at: Optional[datetime] = None
    view_count: Optional[int] = None


class VideoCreate(VideoBase):
    course_id: uuid.UUID


class VideoUpdate(OCWBase):
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    order: Optional[int] = None
    view_count: Optional[int] = None


class VideoRead(VideoBase, TimestampMixin):
    course_id: uuid.UUID
    youtube_url: str = ""
    embed_url: str = ""


class VideoList(OCWBase):
    items: list[VideoRead]
    total: int
    page: int
    page_size: int
    pages: int
