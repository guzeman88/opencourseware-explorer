from __future__ import annotations

import uuid
from typing import Optional

from pydantic import HttpUrl

from app.schemas.base import OCWBase, TimestampMixin


class UniversityBase(OCWBase):
    name: str
    slug: str
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    country: Optional[str] = None
    youtube_channel_id: Optional[str] = None
    source_key: str


class UniversityCreate(UniversityBase):
    pass


class UniversityUpdate(OCWBase):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    country: Optional[str] = None
    youtube_channel_id: Optional[str] = None


class UniversityRead(UniversityBase, TimestampMixin):
    course_count: int = 0


class UniversityList(OCWBase):
    items: list[UniversityRead]
    total: int
    page: int
    page_size: int
    pages: int
