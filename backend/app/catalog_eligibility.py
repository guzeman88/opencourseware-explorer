from __future__ import annotations

import re
from dataclasses import dataclass

from app.catalog_quality import NON_CATALOG_SOURCE_KEYS, NON_COURSE_TITLE_FRAGMENTS


POLICY_VERSION = "v1-shadow"
NON_ENGLISH_SCRIPT_RE = re.compile(
    r"[\u0400-\u052f\u2de0-\u2dff\ua640-\ua69f\u0370-\u03ff"
    r"\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]"
)


@dataclass(frozen=True)
class EligibilityInput:
    source_key: str
    title: str
    is_published: bool
    has_video_lectures: bool
    youtube_playlist_id: str | None
    total_videos: int
    actual_video_count: int


@dataclass(frozen=True)
class EligibilityDecision:
    status: str
    reasons: tuple[str, ...]
    current_catalog_ready: bool


def evaluate_catalog_eligibility(course: EligibilityInput) -> EligibilityDecision:
    """Classify a course without changing current public behavior.

    Definitive exclusions are limited to rules with no ambiguity. Credible video
    evidence, language uncertainty, title-quality concerns, and stale flags are
    preserved for review instead of being hidden automatically.
    """
    title = course.title.strip()
    normalized_title = title.lower()
    title_blocked = title.startswith(("#", "@")) or any(
        fragment in normalized_title for fragment in NON_COURSE_TITLE_FRAGMENTS
    )
    current_catalog_ready = (
        course.is_published
        and course.has_video_lectures
        and course.total_videos > 0
        and course.actual_video_count > 0
        and course.source_key not in NON_CATALOG_SOURCE_KEYS
        and not title_blocked
    )

    if course.source_key in NON_CATALOG_SOURCE_KEYS:
        return EligibilityDecision(
            status="excluded",
            reasons=("excluded_source",),
            current_catalog_ready=current_catalog_ready,
        )

    if course.actual_video_count == 0:
        if course.youtube_playlist_id or course.has_video_lectures:
            return EligibilityDecision(
                status="review",
                reasons=("credible_video_evidence_without_rows",),
                current_catalog_ready=current_catalog_ready,
            )
        return EligibilityDecision(
            status="excluded",
            reasons=("no_video_rows",),
            current_catalog_ready=current_catalog_ready,
        )

    reasons: list[str] = []
    if not course.is_published:
        reasons.append("unpublished_with_video_rows")
    if not course.has_video_lectures:
        reasons.append("video_flag_false_with_video_rows")
    if course.total_videos != course.actual_video_count:
        reasons.append("video_counter_mismatch")
    if NON_ENGLISH_SCRIPT_RE.search(title):
        reasons.append("language_review")
    if title_blocked:
        reasons.append("title_quality_review")

    review_reasons = {
        "unpublished_with_video_rows",
        "video_flag_false_with_video_rows",
        "language_review",
        "title_quality_review",
    }
    status = "review" if review_reasons.intersection(reasons) else "eligible"
    return EligibilityDecision(
        status=status,
        reasons=tuple(reasons) or ("verified_video_rows",),
        current_catalog_ready=current_catalog_ready,
    )
