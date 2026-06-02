from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import case, func, inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import Course, CourseLevel, CourseSubject, CourseSubjectRelevance
from app.models.university import University
from app.models.subject import Subject
from app.schemas.course import CourseCreate, CourseFilters, CourseUpdate
from app.subject_matching import strict_subject_title_condition

MIN_SUBJECT_RELEVANCE_SCORE = 40
_HAS_RELEVANCE_TABLE: bool | None = None


async def _has_relevance_table(db: AsyncSession) -> bool:
    global _HAS_RELEVANCE_TABLE
    if _HAS_RELEVANCE_TABLE is not None:
        return _HAS_RELEVANCE_TABLE

    def check(sync_session) -> bool:
        return sa_inspect(sync_session.get_bind()).has_table("course_subject_relevance")

    try:
        _HAS_RELEVANCE_TABLE = await db.run_sync(check)
    except Exception:
        _HAS_RELEVANCE_TABLE = False
    return _HAS_RELEVANCE_TABLE


async def _subject_has_relevance_scores(db: AsyncSession, subject_slug: str) -> bool:
    if not await _has_relevance_table(db):
        return False

    result = await db.execute(
        select(func.count())
        .select_from(CourseSubjectRelevance)
        .join(Subject, CourseSubjectRelevance.subject_id == Subject.id)
        .where(
            Subject.slug == subject_slug,
            CourseSubjectRelevance.score >= MIN_SUBJECT_RELEVANCE_SCORE,
        )
    )
    return (result.scalar_one() or 0) > 0


async def get_course_by_id(db: AsyncSession, course_id: uuid.UUID) -> Course | None:
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.university),
            selectinload(Course.department),
            selectinload(Course.videos),
            selectinload(Course.course_subjects).selectinload(CourseSubject.subject),
        )
        .where(Course.id == course_id)
    )
    return result.scalar_one_or_none()


async def get_course_by_slug(db: AsyncSession, slug: str) -> Course | None:
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.university),
            selectinload(Course.department),
            selectinload(Course.videos),
            selectinload(Course.course_subjects).selectinload(CourseSubject.subject),
        )
        .where(Course.slug == slug)
    )
    return result.scalar_one_or_none()


async def list_courses(
    db: AsyncSession, filters: CourseFilters
) -> tuple[list[Course], int]:
    query = (
        select(Course)
        .options(
            selectinload(Course.university),
            selectinload(Course.course_subjects).selectinload(CourseSubject.subject),
        )
    )
    count_query = select(func.count()).select_from(Course)
    relevance_scores = None

    # Apply filters
    if filters.q:
        search = f"%{filters.q}%"
        query = query.where(Course.title.ilike(search))
        count_query = count_query.where(Course.title.ilike(search))

    if filters.university_id:
        query = query.where(Course.university_id == filters.university_id)
        count_query = count_query.where(Course.university_id == filters.university_id)

    if filters.university_slug:
        sub = select(University.id).where(University.slug == filters.university_slug)
        query = query.where(Course.university_id.in_(sub))
        count_query = count_query.where(Course.university_id.in_(sub))

    use_strict_subject_relevance = (
        filters.subject_slug is not None and filters.sort_by == "relevance"
    )
    use_scored_subject_relevance = (
        filters.subject_slug is not None
        and filters.sort_by == "relevance"
        and not use_strict_subject_relevance
        and await _subject_has_relevance_scores(db, filters.subject_slug)
    )

    if filters.subject_slug and use_strict_subject_relevance:
        strict_match = strict_subject_title_condition(Course.title, filters.subject_slug)
        query = query.where(strict_match)
        count_query = count_query.where(strict_match)
    elif filters.subject_slug and use_scored_subject_relevance:
        relevance_scores = (
            select(
                CourseSubjectRelevance.course_id,
                func.max(CourseSubjectRelevance.score).label("subject_relevance_score"),
            )
            .join(Subject, CourseSubjectRelevance.subject_id == Subject.id)
            .where(
                Subject.slug == filters.subject_slug,
                CourseSubjectRelevance.score >= MIN_SUBJECT_RELEVANCE_SCORE,
            )
            .group_by(CourseSubjectRelevance.course_id)
            .subquery()
        )
        query = query.join(relevance_scores, Course.id == relevance_scores.c.course_id)
        count_query = count_query.where(
            Course.id.in_(select(relevance_scores.c.course_id))
        )
    elif filters.subject_slug:
        sub = (
            select(CourseSubject.course_id)
            .join(Subject, CourseSubject.subject_id == Subject.id)
            .where(Subject.slug == filters.subject_slug)
        )
        query = query.where(Course.id.in_(sub))
        count_query = count_query.where(Course.id.in_(sub))

    if filters.level:
        query = query.where(Course.level == filters.level)
        count_query = count_query.where(Course.level == filters.level)

    if filters.source_key:
        query = query.where(Course.source_key == filters.source_key)
        count_query = count_query.where(Course.source_key == filters.source_key)

    if filters.has_video_lectures is not None:
        query = query.where(Course.has_video_lectures == filters.has_video_lectures)
        count_query = count_query.where(
            Course.has_video_lectures == filters.has_video_lectures
        )

    if filters.has_thumbnail is True:
        query = query.where(Course.thumbnail_url.isnot(None))
        count_query = count_query.where(Course.thumbnail_url.isnot(None))
    elif filters.has_thumbnail is False:
        query = query.where(Course.thumbnail_url.is_(None))
        count_query = count_query.where(Course.thumbnail_url.is_(None))

    # Sorting
    if filters.sort_by == "relevance" and filters.subject_slug:
        if relevance_scores is not None:
            query = query.order_by(
                relevance_scores.c.subject_relevance_score.desc(),
                Course.view_count.desc(),
                Course.title.asc(),
            )
        else:
            term = filters.subject_slug.replace("-", " ")
            title_match = case((Course.title.ilike(f"%{term}%"), 0), else_=1)
            query = query.order_by(title_match, Course.view_count.desc(), Course.title.asc())
    else:
        sort_col = {
            "title": Course.title,
            "view_count": Course.view_count,
            "created_at": Course.created_at,
            "total_videos": Course.total_videos,
        }.get(filters.sort_by, Course.title)

        if filters.sort_dir == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

    # Pagination
    offset = (filters.page - 1) * filters.page_size
    query = query.offset(offset).limit(filters.page_size)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(query)
    courses = list(result.scalars().all())
    return courses, total


async def create_course(db: AsyncSession, data: CourseCreate) -> Course:
    course = Course(
        **data.model_dump(exclude={"subject_ids"}),
    )
    db.add(course)
    await db.flush()  # get the ID

    for sid in data.subject_ids:
        db.add(CourseSubject(course_id=course.id, subject_id=sid))

    await db.commit()
    await db.refresh(course)
    return course


async def update_course(
    db: AsyncSession, course: Course, data: CourseUpdate
) -> Course:
    update_data = data.model_dump(exclude_unset=True, exclude={"subject_ids"})
    for k, v in update_data.items():
        setattr(course, k, v)

    if data.subject_ids is not None:
        # Replace subjects
        await db.execute(
            CourseSubject.__table__.delete().where(
                CourseSubject.course_id == course.id
            )
        )
        for sid in data.subject_ids:
            db.add(CourseSubject(course_id=course.id, subject_id=sid))

    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(db: AsyncSession, course: Course) -> None:
    await db.delete(course)
    await db.commit()


async def increment_view(db: AsyncSession, course: Course) -> None:
    course.view_count += 1
    await db.commit()
