
import json
import logging
import math

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud import (
    get_course_by_slug,
    get_course_by_id,
    list_courses,
    increment_view,
)
from app.database import get_db
from app.models.course import CourseLevel
from app.schemas.course import (
    CourseFilters,
    CourseList,
    CourseRead,
    CourseSummary,
    VideoSummary,
)
from app.schemas.subject import SubjectSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])

_CACHE_TTL = 60  # seconds
_CACHE_PREFIX = "ocw:courses:"


def _cache_key(filters: CourseFilters) -> str:
    return (
        f"{_CACHE_PREFIX}"
        f"{filters.q}|{filters.university_slug}|{filters.subject_slug}|"
        f"{filters.level}|{filters.source_key}|{filters.has_video_lectures}|"
        f"{filters.is_published}|{filters.page}|{filters.page_size}|"
        f"{filters.sort_by}|{filters.sort_dir}"
    )


async def _get_redis() -> aioredis.Redis | None:
    try:
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=1)
        await r.ping()
        return r
    except Exception:
        return None


async def _get_cached(key: str) -> CourseList | None:
    r = await _get_redis()
    if r is None:
        return None
    try:
        raw = await r.get(key)
        if raw:
            return CourseList.model_validate_json(raw)
    except Exception as exc:
        logger.debug("Redis cache get failed: %s", exc)
    finally:
        await r.aclose()
    return None


async def _set_cached(key: str, val: CourseList) -> None:
    r = await _get_redis()
    if r is None:
        return
    try:
        await r.setex(key, _CACHE_TTL, val.model_dump_json())
    except Exception as exc:
        logger.debug("Redis cache set failed: %s", exc)
    finally:
        await r.aclose()


# ─────────────────────────────────────────────────────────────────────────────


def _safe_col_dict(orm_obj) -> dict:
    """Return only column attributes that are already loaded (no lazy I/O)."""
    insp = sa_inspect(orm_obj)
    result = {}
    for attr in insp.mapper.column_attrs:
        history = insp.attrs[attr.key].history
        # loaded = value in history.unchanged or history.added
        loaded = history.unchanged or history.added
        if loaded:
            result[attr.key] = loaded[0]
        else:
            result[attr.key] = None
    return result


def _build_course_read(course) -> CourseRead:
    subjects = [
        SubjectSummary.model_validate(cs.subject)
        for cs in (course.course_subjects or [])
        if cs.subject
    ]
    videos = [VideoSummary.model_validate(v) for v in (course.videos or [])]
    d = CourseRead.model_validate(_safe_col_dict(course))
    d.university_name = course.university.name if course.university else ""
    d.university_slug = course.university.slug if course.university else ""
    d.department_name = course.department.name if course.department else None
    d.subjects = subjects
    d.videos = videos
    return d


def _build_summary(course) -> CourseSummary:
    subjects = [
        SubjectSummary.model_validate(cs.subject)
        for cs in (course.course_subjects or [])
        if cs.subject
    ]
    d = CourseSummary.model_validate(course)
    d.university_name = course.university.name if course.university else ""
    d.university_slug = course.university.slug if course.university else ""
    d.subjects = subjects
    return d


@router.get("", response_model=CourseList)
async def list_courses_endpoint(
    request: Request,
    q: str | None = Query(None, description="Full-text search"),
    university_slug: str | None = Query(None),
    subject_slug: str | None = Query(None),
    level: str | None = Query(None),
    source_key: str | None = Query(None),
    has_video_lectures: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    sort_by: str = Query("title"),
    sort_dir: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
):
    filters = CourseFilters(
        q=q,
        university_slug=university_slug,
        subject_slug=subject_slug,
        level=CourseLevel(level) if level else None,
        source_key=source_key,
        has_video_lectures=has_video_lectures,
        is_published=True,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    key = _cache_key(filters)
    if cached := await _get_cached(key):
        return cached
    courses, total = await list_courses(db, filters)
    pages = max(1, math.ceil(total / page_size))
    items = [_build_summary(c) for c in courses]
    result = CourseList(items=items, total=total, page=page, page_size=page_size, pages=pages)
    await _set_cached(key, result)
    return result


@router.get("/featured", response_model=CourseList)
async def featured_courses(
    request: Request,
    page_size: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Return most-viewed courses — used for the hero banner."""
    filters = CourseFilters(
        has_video_lectures=True,
        is_published=True,
        page=1,
        page_size=page_size,
        sort_by="view_count",
        sort_dir="desc",
    )
    key = _cache_key(filters)
    if cached := await _get_cached(key):
        return cached
    courses, total = await list_courses(db, filters)
    items = [_build_summary(c) for c in courses]
    result = CourseList(items=items, total=total, page=1, page_size=page_size, pages=1)
    await _set_cached(key, result)
    return result


@router.get("/{slug_or_id}", response_model=CourseRead)
async def get_course(slug_or_id: str, db: AsyncSession = Depends(get_db)):
    import uuid as _uuid

    course = None
    try:
        uid = _uuid.UUID(slug_or_id)
        course = await get_course_by_id(db, uid)
    except ValueError:
        course = await get_course_by_slug(db, slug_or_id)

    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Fire-and-forget view increment (best effort)
    try:
        await increment_view(db, course)
    except Exception:
        pass

    return _build_course_read(course)

