
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import list_universities, get_university_by_slug, get_university_by_id
from app.crud import list_courses
from app.database import get_db
from app.models.course import Course
from app.schemas.course import CourseFilters, CourseList, CourseSummary
from app.schemas.university import UniversityList, UniversityRead

router = APIRouter(prefix="/universities", tags=["universities"])


def _enrich_uni(uni, course_count: int = 0) -> UniversityRead:
    d = UniversityRead.model_validate(uni)
    d.course_count = course_count
    return d


async def _get_course_counts(db: AsyncSession, university_ids: list) -> dict:
    """Return {university_id: course_count} for the given ids in one query."""
    if not university_ids:
        return {}
    result = await db.execute(
        select(Course.university_id, func.count(Course.id).label("cnt"))
        .where(Course.university_id.in_(university_ids))
        .group_by(Course.university_id)
    )
    return {row.university_id: row.cnt for row in result}


@router.get("", response_model=UniversityList)
async def list_universities_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    q: str | None = Query(None),
    is_institution: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    unis, total = await list_universities(
        db, page=page, page_size=page_size, q=q, is_institution=is_institution
    )
    pages = max(1, math.ceil(total / page_size))
    counts = await _get_course_counts(db, [u.id for u in unis])
    items = [_enrich_uni(u, counts.get(u.id, 0)) for u in unis]
    return UniversityList(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{slug}", response_model=UniversityRead)
async def get_university(slug: str, db: AsyncSession = Depends(get_db)):
    uni = await get_university_by_slug(db, slug)
    if uni is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found")
    return _enrich_uni(uni)


@router.get("/{slug}/courses", response_model=CourseList)
async def get_university_courses(
    slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    level: str | None = Query(None),
    has_video_lectures: bool | None = Query(None),
    sort_by: str = Query("title"),
    sort_dir: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
):
    from app.models.course import CourseLevel

    filters = CourseFilters(
        university_slug=slug,
        page=page,
        page_size=page_size,
        level=CourseLevel(level) if level else None,
        has_video_lectures=has_video_lectures,
        is_published=True,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    courses, total = await list_courses(db, filters)
    pages = max(1, math.ceil(total / page_size))
    items = [_course_to_summary(c) for c in courses]
    return CourseList(items=items, total=total, page=page, page_size=page_size, pages=pages)


def _course_to_summary(course) -> CourseSummary:
    from app.schemas.subject import SubjectSummary

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
