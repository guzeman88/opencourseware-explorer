
import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import list_courses
from app.database import get_db
from app.models.course import CourseLevel
from app.schemas.course import CourseFilters, CourseList, CourseSummary
from app.schemas.subject import SubjectSummary

router = APIRouter(prefix="/search", tags=["search"])
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=CourseList)
@limiter.limit("30/minute")
async def search_courses(
    request: Request,
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    level: str | None = Query(None),
    source_key: str | None = Query(None),
    has_video_lectures: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    filters = CourseFilters(
        q=q,
        level=CourseLevel(level) if level else None,
        source_key=source_key,
        has_video_lectures=has_video_lectures,
        page=page,
        page_size=page_size,
        sort_by="view_count",
        sort_dir="desc",
    )
    courses, total = await list_courses(db, filters)
    pages = max(1, math.ceil(total / page_size))

    items = []
    for c in courses:
        subjects = [
            SubjectSummary.model_validate(cs.subject)
            for cs in (c.course_subjects or [])
            if cs.subject
        ]
        s = CourseSummary.model_validate(c)
        s.university_name = c.university.name if c.university else ""
        s.university_slug = c.university.slug if c.university else ""
        s.subjects = subjects
        items.append(s)

    return CourseList(items=items, total=total, page=page, page_size=page_size, pages=pages)
