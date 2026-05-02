from __future__ import annotations

import uuid
from typing import Optional

from app.schemas.base import OCWBase, TimestampMixin


class SubjectBase(OCWBase):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(OCWBase):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None


class SubjectSummary(SubjectBase, TimestampMixin):
    """Flat subject used inside course responses (no children to avoid lazy-load)."""

    course_count: int = 0

    model_config = {"from_attributes": True}


class SubjectRead(SubjectBase, TimestampMixin):
    course_count: int = 0
    children: list[SubjectRead] = []

    model_config = {"from_attributes": True}


SubjectRead.model_rebuild()


class SubjectList(OCWBase):
    items: list[SubjectRead]
    total: int
    page: int
    page_size: int
    pages: int
