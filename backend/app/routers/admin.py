import asyncio
import json
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_course,
    create_university,
    delete_course,
    delete_university,
    get_course_by_id,
    get_course_by_slug,
    get_university_by_id,
    get_university_by_slug,
    list_courses,
    list_universities,
    update_course,
    update_university,
)
from app.database import AsyncSessionLocal, get_db
from app.models.course import Course
from app.models.scraper_job import JobStatus, ScraperJob
from app.models.university import University
from app.models.subject import Subject
from app.models.video import Video
from app.schemas.admin import (
    LoginRequest,
    ScraperJobCreate,
    ScraperJobList,
    ScraperJobRead,
    StatsResponse,
    TokenResponse,
)
from app.schemas.course import CourseCreate, CourseFilters, CourseList, CourseRead, CourseUpdate
from app.schemas.subject import SubjectRead
from app.schemas.university import UniversityCreate, UniversityList, UniversityRead, UniversityUpdate
from app.services import authenticate_user, create_access_token, require_admin
from app.services.deps import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])
limiter = Limiter(key_func=get_remote_address)


# ─── Auth ────────────────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token)


# ─── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse, dependencies=[Depends(require_admin)])
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_universities = (
        await db.execute(select(func.count()).select_from(University))
    ).scalar_one()
    total_courses = (
        await db.execute(select(func.count()).select_from(Course))
    ).scalar_one()
    total_videos = (
        await db.execute(select(func.count()).select_from(Video))
    ).scalar_one()
    total_subjects = (
        await db.execute(select(func.count()).select_from(Subject))
    ).scalar_one()
    courses_with_video = (
        await db.execute(
            select(func.count()).select_from(Course).where(Course.has_video_lectures == True)
        )
    ).scalar_one()

    pending_review = (
        await db.execute(
            select(func.count()).select_from(Course).where(Course.is_published == False)
        )
    ).scalar_one()

    source_rows = await db.execute(
        select(Course.source_key, func.count(Course.id))
        .group_by(Course.source_key)
        .order_by(func.count(Course.id).desc())
    )
    sources = [{"source_key": r[0], "count": r[1]} for r in source_rows]

    return StatsResponse(
        total_universities=total_universities,
        total_courses=total_courses,
        total_videos=total_videos,
        total_subjects=total_subjects,
        courses_with_video=courses_with_video,
        pending_review=pending_review,
        sources=sources,
    )


# ─── Universities (Admin CRUD) ────────────────────────────────────────────────

@router.get("/universities", response_model=UniversityList, dependencies=[Depends(require_admin)])
async def admin_list_universities(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    unis, total = await list_universities(db, page=page, page_size=page_size)
    pages = max(1, math.ceil(total / page_size))
    items = [UniversityRead.model_validate(u) for u in unis]
    return UniversityList(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.post("/universities", response_model=UniversityRead, status_code=201,
             dependencies=[Depends(require_admin)])
async def admin_create_university(data: UniversityCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_university_by_slug(db, data.slug)
    if existing:
        raise HTTPException(status_code=409, detail="University with this slug already exists")
    uni = await create_university(db, data)
    return UniversityRead.model_validate(uni)


@router.put("/universities/{uni_id}", response_model=UniversityRead,
            dependencies=[Depends(require_admin)])
async def admin_update_university(
    uni_id: uuid.UUID, data: UniversityUpdate, db: AsyncSession = Depends(get_db)
):
    uni = await get_university_by_id(db, uni_id)
    if uni is None:
        raise HTTPException(status_code=404, detail="Not found")
    updated = await update_university(db, uni, data)
    return UniversityRead.model_validate(updated)


@router.delete("/universities/{uni_id}", status_code=204,
               dependencies=[Depends(require_admin)])
async def admin_delete_university(uni_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    uni = await get_university_by_id(db, uni_id)
    if uni is None:
        raise HTTPException(status_code=404, detail="Not found")
    await delete_university(db, uni)


# ─── Courses (Admin CRUD) ─────────────────────────────────────────────────────

@router.get("/courses", response_model=CourseList, dependencies=[Depends(require_admin)])
async def admin_list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    q: Optional[str] = Query(None),
    source_key: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # Show ALL courses (no is_published filter) in admin list
    filters = CourseFilters(page=page, page_size=page_size, q=q, source_key=source_key)
    courses, total = await list_courses(db, filters)
    pages = max(1, math.ceil(total / page_size))
    from app.routers.courses import _build_summary
    items = [_build_summary(c) for c in courses]
    return CourseList(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/courses/pending-review", response_model=CourseList, dependencies=[Depends(require_admin)])
async def admin_pending_review_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    q: Optional[str] = Query(None),
    source_key: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return non-video courses that are hidden from the public site, pending review."""
    filters = CourseFilters(
        page=page, page_size=page_size, q=q, source_key=source_key, is_published=False
    )
    courses, total = await list_courses(db, filters)
    pages = max(1, math.ceil(total / page_size))
    from app.routers.courses import _build_summary
    items = [_build_summary(c) for c in courses]
    return CourseList(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.patch("/courses/{course_id}/publish", response_model=CourseRead,
              dependencies=[Depends(require_admin)])
async def admin_set_course_published(
    course_id: uuid.UUID,
    published: bool = Query(..., description="True to publish, False to unpublish"),
    db: AsyncSession = Depends(get_db),
):
    """Publish or unpublish a single course."""
    course = await get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Not found")
    updated = await update_course(db, course, CourseUpdate(is_published=published))
    from app.routers.courses import _build_course_read
    return _build_course_read(updated)


@router.post("/courses", response_model=CourseRead, status_code=201,
             dependencies=[Depends(require_admin)])
async def admin_create_course(data: CourseCreate, db: AsyncSession = Depends(get_db)):
    course = await create_course(db, data)
    from app.routers.courses import _build_course_read
    return _build_course_read(course)


@router.put("/courses/{course_id}", response_model=CourseRead,
            dependencies=[Depends(require_admin)])
async def admin_update_course(
    course_id: uuid.UUID, data: CourseUpdate, db: AsyncSession = Depends(get_db)
):
    course = await get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Not found")
    updated = await update_course(db, course, data)
    from app.routers.courses import _build_course_read
    return _build_course_read(updated)


@router.delete("/courses/{course_id}", status_code=204,
               dependencies=[Depends(require_admin)])
async def admin_delete_course(course_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    course = await get_course_by_id(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Not found")
    await delete_course(db, course)


# ─── Scraper Jobs ─────────────────────────────────────────────────────────────

@router.get("/scraper/jobs", response_model=ScraperJobList, dependencies=[Depends(require_admin)])
async def list_scraper_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import desc

    q = (
        select(ScraperJob)
        .order_by(desc(ScraperJob.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    count_q = select(func.count()).select_from(ScraperJob)
    jobs = list((await db.execute(q)).scalars().all())
    total = (await db.execute(count_q)).scalar_one()
    return ScraperJobList(
        items=[ScraperJobRead.model_validate(j) for j in jobs], total=total
    )


@router.post("/scraper/jobs", response_model=ScraperJobRead, status_code=202,
             dependencies=[Depends(require_admin)])
async def trigger_scraper_job(
    data: ScraperJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    job = ScraperJob(source=data.source, config_json=data.config_json)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    background_tasks.add_task(_run_scraper_background, job.id, data.source)
    return ScraperJobRead.model_validate(job)


async def _run_scraper_background(job_id: uuid.UUID, source: str) -> None:
    """Run the appropriate scraper in the background."""
    async with AsyncSessionLocal() as db:
        job = (
            await db.execute(select(ScraperJob).where(ScraperJob.id == job_id))
        ).scalar_one_or_none()
        if job is None:
            return

        job.status = JobStatus.running
        job.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            # Dynamically import and run the scraper
            from scraper_runner import run_scraper  # type: ignore
            counts = await run_scraper(source, db)
            job.courses_scraped = counts.get("courses", 0)
            job.videos_scraped = counts.get("videos", 0)
            job.status = JobStatus.completed
        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)[:2000]
        finally:
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
