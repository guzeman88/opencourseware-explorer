from __future__ import annotations

import math
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.university import University
from app.schemas.university import UniversityCreate, UniversityUpdate


async def get_university_by_id(db: AsyncSession, uid: uuid.UUID) -> University | None:
    result = await db.execute(
        select(University)
        .options(selectinload(University.departments))
        .where(University.id == uid)
    )
    return result.scalar_one_or_none()


async def get_university_by_slug(db: AsyncSession, slug: str) -> University | None:
    result = await db.execute(
        select(University)
        .options(selectinload(University.departments))
        .where(University.slug == slug)
    )
    return result.scalar_one_or_none()


async def list_universities(
    db: AsyncSession, page: int = 1, page_size: int = 50, q: str | None = None
) -> tuple[list[University], int]:
    query = select(University)
    count_query = select(func.count()).select_from(University)

    if q:
        search = f"%{q}%"
        query = query.where(University.name.ilike(search))
        count_query = count_query.where(University.name.ilike(search))

    query = query.order_by(University.name.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    total = (await db.execute(count_query)).scalar_one()
    rows = list((await db.execute(query)).scalars().all())
    return rows, total


async def create_university(db: AsyncSession, data: UniversityCreate) -> University:
    uni = University(**data.model_dump())
    db.add(uni)
    await db.commit()
    await db.refresh(uni)
    return uni


async def upsert_university(
    db: AsyncSession, source_key: str, slug: str, data: dict
) -> University:
    """Insert or update a university by source_key + slug."""
    result = await db.execute(
        select(University).where(University.slug == slug)
    )
    uni = result.scalar_one_or_none()
    if uni is None:
        uni = University(**data)
        db.add(uni)
    else:
        for k, v in data.items():
            setattr(uni, k, v)
    await db.commit()
    await db.refresh(uni)
    return uni


async def update_university(
    db: AsyncSession, uni: University, data: UniversityUpdate
) -> University:
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(uni, k, v)
    await db.commit()
    await db.refresh(uni)
    return uni


async def delete_university(db: AsyncSession, uni: University) -> None:
    await db.delete(uni)
    await db.commit()
