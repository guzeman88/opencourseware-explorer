from __future__ import annotations

from sqlalchemy import and_, exists, or_, select

from app.models.course import Course
from app.models.video import Video


NON_CATALOG_SOURCE_KEYS = {"nptel"}

# Playlist-level titles that should never be treated as public courses.
NON_COURSE_TITLE_FRAGMENTS = (
    "#short",
    "admissions",
    "alumni",
    "anniversary",
    "campus life",
    "ceremony",
    "commencement",
    "convocation",
    "episode",
    "family weekend",
    "graduation",
    "highlights",
    "homecoming",
    "information session",
    "live clips",
    "orientation",
    "promo",
    "promotional",
    "recap",
    "reunion",
    "season ",
    "student spotlight",
    "teaser",
    "trailer",
    "year in review",
)


def catalog_ready_condition(course_model=Course):
    """SQL predicate for courses allowed in the public catalog."""
    title_blockers = [
        course_model.title.ilike(f"%{fragment}%")
        for fragment in NON_COURSE_TITLE_FRAGMENTS
    ]

    return and_(
        course_model.is_published.is_(True),
        course_model.has_video_lectures.is_(True),
        course_model.total_videos > 0,
        ~course_model.source_key.in_(NON_CATALOG_SOURCE_KEYS),
        exists(select(Video.id).where(Video.course_id == course_model.id)),
        ~or_(*title_blockers),
    )
