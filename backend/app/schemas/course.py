from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import field_validator
from app.models.course import CourseLevel
from app.schemas.base import OCWBase, TimestampMixin
from app.schemas.subject import SubjectRead, SubjectSummary


class VideoSummary(OCWBase, TimestampMixin):
    youtube_id: str
    title: str
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    order: int
    silence_segments: Optional[list[list[float]]] = None


class CourseBase(OCWBase):
    course_number: Optional[str] = None
    title: str
    slug: str
    description: Optional[str] = None
    level: CourseLevel = CourseLevel.other
    source_url: Optional[str] = None
    source_key: str
    thumbnail_url: Optional[str] = None
    instructor: Optional[str] = None
    year: Optional[int] = None
    semester: Optional[str] = None
    has_video_lectures: bool = False
    has_lecture_notes: bool = False
    has_exams: bool = False
    lecture_notes_url: Optional[str] = None
    exams_url: Optional[str] = None
    youtube_playlist_id: Optional[str] = None
    total_videos: int = 0
    total_duration_seconds: int = 0


class CourseCreate(CourseBase):
    university_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    subject_ids: list[uuid.UUID] = []


class CourseUpdate(OCWBase):
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[CourseLevel] = None
    thumbnail_url: Optional[str] = None
    instructor: Optional[str] = None
    year: Optional[int] = None
    semester: Optional[str] = None
    has_video_lectures: Optional[bool] = None
    has_lecture_notes: Optional[bool] = None
    has_exams: Optional[bool] = None
    lecture_notes_url: Optional[str] = None
    exams_url: Optional[str] = None
    youtube_playlist_id: Optional[str] = None
    subject_ids: Optional[list[uuid.UUID]] = None


class CourseRead(CourseBase, TimestampMixin):
    university_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    university_name: str = ""
    university_slug: str = ""
    department_name: Optional[str] = None
    view_count: int = 0
    subjects: list[SubjectSummary] = []
    videos: list[VideoSummary] = []


class CourseSummary(OCWBase, TimestampMixin):
    """Lightweight version for list views."""
    course_number: Optional[str] = None
    title: str
    slug: str
    level: CourseLevel
    source_key: str
    source_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    instructor: Optional[str] = None
    year: Optional[int] = None
    has_video_lectures: bool
    has_lecture_notes: bool = False
    has_exams: bool = False
    total_videos: int
    university_id: uuid.UUID
    university_name: str = ""
    university_slug: str = ""
    subjects: list[SubjectSummary] = []


class CourseList(OCWBase):
    items: list[CourseSummary]
    total: int
    page: int
    page_size: int
    pages: int


class CourseFilters(OCWBase):
    """Query parameters for filtering courses."""
    q: Optional[str] = None
    university_id: Optional[uuid.UUID] = None
    university_slug: Optional[str] = None
    subject_slug: Optional[str] = None
    level: Optional[CourseLevel] = None
    source_key: Optional[str] = None
    has_video_lectures: Optional[bool] = None
    page: int = 1
    page_size: int = 24
    sort_by: str = "title"  # title | view_count | created_at | total_videos | relevance
    sort_dir: str = "asc"   # asc | desc

    @field_validator("q")
    @classmethod
    def _clamp_q(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 200:
            raise ValueError("Search query must not exceed 200 characters")
        return v

    @field_validator("sort_by")
    @classmethod
    def _valid_sort_by(cls, v: str) -> str:
        allowed = {"title", "view_count", "created_at", "total_videos", "relevance"}
        if v not in allowed:
            return "title"
        return v

    @field_validator("sort_dir")
    @classmethod
    def _valid_sort_dir(cls, v: str) -> str:
        if v not in {"asc", "desc"}:
            return "asc"
        return v
