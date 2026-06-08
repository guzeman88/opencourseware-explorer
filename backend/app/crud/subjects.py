from __future__ import annotations

import uuid

from sqlalchemy import func, inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.catalog_quality import catalog_ready_condition
from app.models.course import Course, CourseSubject
from app.models.catalog_eligibility import SubjectCatalogCount
from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate
from app.subject_counts import STRICT_COUNT_POLICY_VERSION
from app.subject_matching import strict_subject_matches_title


_HAS_SUBJECT_COUNT_TABLE: bool | None = None


async def _has_subject_count_table(db: AsyncSession) -> bool:
    global _HAS_SUBJECT_COUNT_TABLE
    if _HAS_SUBJECT_COUNT_TABLE is not None:
        return _HAS_SUBJECT_COUNT_TABLE

    def check(sync_session) -> bool:
        return sa_inspect(sync_session.get_bind()).has_table("subject_catalog_counts")

    try:
        _HAS_SUBJECT_COUNT_TABLE = await db.run_sync(check)
    except Exception:
        _HAS_SUBJECT_COUNT_TABLE = False
    return _HAS_SUBJECT_COUNT_TABLE


async def get_subject_by_slug(db: AsyncSession, slug: str) -> Subject | None:
    ccsq = _course_count_subq()
    result = await db.execute(
        select(Subject, func.coalesce(ccsq.c.course_count, 0).label("course_count"))
        .outerjoin(ccsq, Subject.id == ccsq.c.subject_id)
        .options(selectinload(Subject.children))
        .where(Subject.slug == slug)
    )
    row = result.one_or_none()
    if row is None:
        return None
    subj, count = row
    subj.course_count = count
    return subj


def _course_count_subq():
    return (
        select(
            CourseSubject.subject_id,
            func.count(CourseSubject.course_id).label("course_count"),
        )
        .join(Course, Course.id == CourseSubject.course_id)
        .where(catalog_ready_condition(Course))
        .group_by(CourseSubject.subject_id)
        .subquery()
    )


async def list_subjects(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 100,
    parent_id: uuid.UUID | None = None,
    top_level_only: bool = False,
    strict_counts: bool = False,
) -> tuple[list[Subject], int]:
    ccsq = _course_count_subq()

    query = (
        select(Subject, func.coalesce(ccsq.c.course_count, 0).label("course_count"))
        .outerjoin(ccsq, Subject.id == ccsq.c.subject_id)
        .options(selectinload(Subject.children))
    )
    count_q = select(func.count()).select_from(Subject)

    if top_level_only:
        query = query.where(Subject.parent_id.is_(None))
        count_q = count_q.where(Subject.parent_id.is_(None))
    elif parent_id is not None:
        query = query.where(Subject.parent_id == parent_id)
        count_q = count_q.where(Subject.parent_id == parent_id)

    query = query.order_by(Subject.name.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    total = (await db.execute(count_q)).scalar_one()
    rows = list((await db.execute(query)).all())

    # Attach course_count to Subject instances so model_validate can read it
    subjects = []
    for row in rows:
        subj = row[0]
        subj.course_count = row[1]
        subjects.append(subj)

    if strict_counts and subjects:
        persisted_counts: dict[uuid.UUID, int] = {}
        if await _has_subject_count_table(db):
            persisted_counts = {
                subject_id: course_count
                for subject_id, course_count in (
                    await db.execute(
                        select(
                            SubjectCatalogCount.subject_id,
                            SubjectCatalogCount.course_count,
                        ).where(
                            SubjectCatalogCount.subject_id.in_(
                                [subject.id for subject in subjects]
                            ),
                            SubjectCatalogCount.policy_version
                            == STRICT_COUNT_POLICY_VERSION,
                        )
                    )
                )
            }

        if persisted_counts:
            for subj in subjects:
                subj.course_count = persisted_counts.get(subj.id, 0)
        else:
            titles = list(
                (
                    await db.execute(
                        select(Course.title).where(catalog_ready_condition(Course))
                    )
                )
                .scalars()
                .all()
            )
            for subj in subjects:
                subj.course_count = sum(
                    1
                    for title in titles
                    if strict_subject_matches_title(title, subj.slug)
                )

    return subjects, total


async def get_or_create_subject(db: AsyncSession, name: str, slug: str) -> Subject:
    result = await db.execute(select(Subject).where(Subject.slug == slug))
    subj = result.scalar_one_or_none()
    if subj is None:
        subj = Subject(name=name, slug=slug)
        db.add(subj)
        await db.flush()
    return subj


async def create_subject(db: AsyncSession, data: SubjectCreate) -> Subject:
    subj = Subject(**data.model_dump())
    db.add(subj)
    await db.commit()
    await db.refresh(subj)
    return subj
