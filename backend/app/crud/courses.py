from __future__ import annotations

import math
import uuid
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import Course, CourseLevel, CourseSubject
from app.models.university import University
from app.models.subject import Subject
from app.schemas.course import CourseCreate, CourseFilters, CourseUpdate


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

    if filters.subject_slug:
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

    # Sorting
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
