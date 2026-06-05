from __future__ import annotations

from sqlalchemy import and_, exists, or_, select

from app.models.course import Course
from app.models.video import Video


NON_CATALOG_SOURCE_KEYS = {"nptel"}

# Playlist-level titles that should never be treated as public courses.
NON_COURSE_TITLE_FRAGMENTS = (
    "about ",
    "#short",
    "admissions",
    "alumni",
    "anniversary",
    "annual review",
    "apply to",
    "around campus",
    "best of",
    "campus life",
    "centenary lectures",
    "challenge",
    "ceremony",
    "colloquium",
    "commencement",
    "competition",
    "conference",
    "congregation",
    "convocation",
    "conversation with",
    "covid",
    "departmental day",
    "election",
    "episode",
    "event recordings",
    "events",
    "family weekend",
    "forum",
    "graduation",
    "groupe calcul",
    "help sessions",
    "heures avec",
    "highlights",
    "homework, exams",
    "homecoming",
    "information session",
    "interview",
    "lecture series",
    "live clips",
    "meeting",
    "minutes to change",
    "orientation",
    "playlist",
    "programme",
    "programs",
    "promo",
    "promotional",
    "recap",
    "research at",
    "reunion",
    "season ",
    "seminar",
    "special talks",
    "stories",
    "student life",
    "student spotlight",
    "student lectures",
    "symposium",
    "teaser",
    "trailer",
    "video series",
    "workshop",
    "year in review",
    "\" series",
    "colóquio",
    "comunauté",
    "conferência",
    "conférence",
    "encuentro",
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
        ~course_model.title.like("#%"),
        ~course_model.title.like("@%"),
        ~or_(*title_blockers),
    )
