from __future__ import annotations

from typing import Optional

from app.schemas.base import OCWBase, TimestampMixin
from app.models.scraper_job import JobStatus


class ScraperJobCreate(OCWBase):
    source: str
    config_json: Optional[str] = None


class ScraperJobRead(OCWBase, TimestampMixin):
    source: str
    status: JobStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    courses_scraped: int
    videos_scraped: int
    error_message: Optional[str] = None


class ScraperJobList(OCWBase):
    items: list[ScraperJobRead]
    total: int


class TokenResponse(OCWBase):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(OCWBase):
    email: str
    password: str


class StatsResponse(OCWBase):
    total_universities: int
    total_courses: int
    total_videos: int
    total_subjects: int
    courses_with_video: int
    sources: list[dict]
