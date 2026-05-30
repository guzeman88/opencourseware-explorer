from __future__ import annotations

import re
from typing import Optional

from pydantic import EmailStr, field_validator

from app.schemas.base import OCWBase, TimestampMixin
from app.models.scraper_job import JobStatus

_SOURCE_RE = re.compile(r"^[a-z0-9_-]{1,100}$")


class ScraperJobCreate(OCWBase):
    source: str
    config_json: Optional[str] = None

    @field_validator("source")
    @classmethod
    def _valid_source(cls, v: str) -> str:
        if not _SOURCE_RE.match(v):
            raise ValueError(
                "source must be 1–100 lowercase alphanumeric characters, underscores, or hyphens"
            )
        return v


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
    email: EmailStr
    password: str


class StatsResponse(OCWBase):
    total_universities: int
    total_courses: int
    total_videos: int
    total_subjects: int
    courses_with_video: int
    pending_review: int
    sources: list[dict]
