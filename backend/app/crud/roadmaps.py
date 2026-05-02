from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap, RoadmapEntry
from app.models.university import University


async def list_roadmaps(
    db: AsyncSession,
    university_slug: str | None = None,
    major: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Roadmap], int]:
    q = (
        select(Roadmap)
        .join(University, Roadmap.university_id == University.id)
        .options(
            selectinload(Roadmap.university),
            selectinload(Roadmap.entries),
        )
    )
    if university_slug:
        q = q.where(University.slug == university_slug)
    if major:
        q = q.where(func.lower(Roadmap.major).contains(major.lower()))

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    q = q.order_by(University.name, Roadmap.title)
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    return list(rows), total


async def get_roadmap_by_slug(db: AsyncSession, slug: str) -> Roadmap | None:
    q = (
        select(Roadmap)
        .where(Roadmap.slug == slug)
        .options(
            selectinload(Roadmap.university),
            selectinload(Roadmap.entries).selectinload(RoadmapEntry.course),
        )
    )
    return (await db.execute(q)).scalar_one_or_none()


async def list_roadmaps_by_university(
    db: AsyncSession, university_id: uuid.UUID
) -> list[Roadmap]:
    q = (
        select(Roadmap)
        .where(Roadmap.university_id == university_id)
        .options(selectinload(Roadmap.university))
        .order_by(Roadmap.title)
    )
    return list((await db.execute(q)).scalars().all())
