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
from app.subject_counts import MIN_SUBJECT_RELEVANCE_SCORE, STRICT_COUNT_POLICY_VERSION
from app.subject_matching import strict_subject_matches_title


_HAS_COUNTS_TABLE: bool | None = None
_HAS_RELEVANCE_TABLE: bool | None = None


async def _has_subject_count_table(db: AsyncSession) -> bool:
    global _HAS_COUNTS_TABLE
    if _HAS_COUNTS_TABLE is not None:
        return _HAS_COUNTS_TABLE

    def check(sync_session) -> bool:
        return sa_inspect(sync_session.get_bind()).has_table("subject_catalog_counts")

    try:
        _HAS_COUNTS_TABLE = await db.run_sync(check)
    except Exception:
        _HAS_COUNTS_TABLE = False
    return _HAS_COUNTS_TABLE


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


async def get_subject_by_slug(db: AsyncSession, slug: str) -> Subject | None:
    ccsq = await _build_count_subq(db)
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


def _course_count_from_tags():
    """Count catalog-ready courses per subject from explicit course_subjects tags."""
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


def _course_count_from_tags_and_relevance():
    """Count catalog-ready courses per subject from both course_subjects
    (explicit tags) and course_subject_relevance (scored associations)."""
    from app.models.course import CourseSubjectRelevance

    tagged = (
        select(
            CourseSubject.subject_id,
            CourseSubject.course_id,
        )
        .join(Course, Course.id == CourseSubject.course_id)
        .where(catalog_ready_condition(Course))
    )

    scored = (
        select(
            CourseSubjectRelevance.subject_id,
            CourseSubjectRelevance.course_id,
        )
        .join(Course, Course.id == CourseSubjectRelevance.course_id)
        .where(
            CourseSubjectRelevance.score >= MIN_SUBJECT_RELEVANCE_SCORE,
            catalog_ready_condition(Course),
        )
    )

    combined = tagged.union(scored).subquery()

    return (
        select(
            combined.c.subject_id,
            func.count(func.distinct(combined.c.course_id)).label("course_count"),
        )
        .group_by(combined.c.subject_id)
        .subquery()
    )


async def _build_count_subq(db: AsyncSession):
    """Choose the best available count source automatically.

    Uses the combined (course_subjects ∪ course_subject_relevance) subquery
    when the relevance table exists, otherwise falls back to course_subjects alone.
    Both produce counts consistent with the subject detail page
    (catalog_ready_condition via course-to-subject associations).
    """
    if await _has_relevance_table(db):
        return _course_count_from_tags_and_relevance()
    return _course_count_from_tags()


async def _load_persisted_counts(
    db: AsyncSession, subject_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    """Load pre-computed title-matched counts from subject_catalog_counts."""
    rows = (
        await db.execute(
            select(
                SubjectCatalogCount.subject_id,
                SubjectCatalogCount.course_count,
            ).where(
                SubjectCatalogCount.subject_id.in_(subject_ids),
                SubjectCatalogCount.policy_version == STRICT_COUNT_POLICY_VERSION,
            )
        )
    ).all()
    return {subject_id: course_count for subject_id, course_count in rows}


async def list_subjects(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 100,
    parent_id: uuid.UUID | None = None,
    top_level_only: bool = False,
    strict_counts: bool = False,
) -> tuple[list[Subject], int]:
    # Build the count subquery — auto-selects the best source available
    # (tags + relevance if the relevance table exists, tags alone otherwise).
    # These counts are consistent with the subject detail page because both
    # use catalog_ready_condition + course_subjects-based filtering.
    ccsq = await _build_count_subq(db)

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

    subjects: list[Subject] = []
    for row in rows:
        subj = row[0]
        subj.course_count = row[1]
        subjects.append(subj)

    # When strict_counts is requested, use title-matched counts. Prefer
    # pre-computed counts from subject_catalog_counts when available;
    # otherwise fall back to runtime strict_subject_matches_title.
    if strict_counts and subjects:
        persisted = {}
        if await _has_subject_count_table(db):
            persisted = await _load_persisted_counts(
                db, [s.id for s in subjects]
            )

        if persisted:
            for subj in subjects:
                if subj.id in persisted:
                    subj.course_count = persisted[subj.id]
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
