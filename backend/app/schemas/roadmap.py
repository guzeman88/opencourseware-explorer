from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel


class RoadmapEntrySummary(BaseModel):
    id: uuid.UUID
    position: int
    course_number: Optional[str] = None
    course_title: str
    category: Optional[str] = None
    semester: Optional[str] = None
    year_in_program: Optional[int] = None
    is_required: bool
    units: Optional[int] = None
    notes: Optional[str] = None
    # Linked course fields (if matched in DB)
    course_id: Optional[uuid.UUID] = None
    course_slug: Optional[str] = None
    subject_slug: Optional[str] = None

    model_config = {"from_attributes": True}


class RoadmapSummary(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    degree_type: Optional[str] = None
    major: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    estimated_years: Optional[int] = None
    website_url: Optional[str] = None
    university_id: uuid.UUID
    university_name: Optional[str] = None
    university_slug: Optional[str] = None
    entry_count: int = 0

    model_config = {"from_attributes": True}


class RoadmapRead(RoadmapSummary):
    entries: list[RoadmapEntrySummary] = []

    model_config = {"from_attributes": True}


class PaginatedRoadmaps(BaseModel):
    items: list[RoadmapSummary]
    total: int
    page: int
    page_size: int
