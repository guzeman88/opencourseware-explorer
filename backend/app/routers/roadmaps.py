from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import roadmaps as crud
from app.database import get_db
from app.schemas.roadmap import PaginatedRoadmaps, RoadmapRead, RoadmapSummary

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


def _build_summary(rm) -> RoadmapSummary:
    return RoadmapSummary(
        id=rm.id,
        slug=rm.slug,
        title=rm.title,
        degree_type=rm.degree_type,
        major=rm.major,
        department=rm.department,
        description=rm.description,
        estimated_years=rm.estimated_years,
        website_url=rm.website_url,
        university_id=rm.university_id,
        university_name=rm.university.name if rm.university else None,
        university_slug=rm.university.slug if rm.university else None,
        entry_count=len(rm.entries) if hasattr(rm, "entries") and rm.entries else 0,
    )


def _build_read(rm) -> RoadmapRead:
    from app.schemas.roadmap import RoadmapEntrySummary

    entries = [
        RoadmapEntrySummary(
            id=e.id,
            position=e.position,
            course_number=e.course_number,
            course_title=e.course_title,
            category=e.category,
            semester=e.semester,
            year_in_program=e.year_in_program,
            is_required=e.is_required,
            units=e.units,
            notes=e.notes,
            course_id=e.course_id,
            course_slug=e.course.slug if e.course else None,
            subject_slug=e.subject_slug,
        )
        for e in (rm.entries or [])
    ]

    return RoadmapRead(
        id=rm.id,
        slug=rm.slug,
        title=rm.title,
        degree_type=rm.degree_type,
        major=rm.major,
        department=rm.department,
        description=rm.description,
        estimated_years=rm.estimated_years,
        website_url=rm.website_url,
        university_id=rm.university_id,
        university_name=rm.university.name if rm.university else None,
        university_slug=rm.university.slug if rm.university else None,
        entry_count=len(entries),
        entries=entries,
    )


@router.get("", response_model=PaginatedRoadmaps)
async def list_roadmaps(
    university: Optional[str] = Query(None, description="Filter by university slug"),
    major: Optional[str] = Query(None, description="Filter by major name (partial match)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    items, total = await crud.list_roadmaps(db, university_slug=university, major=major, page=page, page_size=page_size)
    return PaginatedRoadmaps(
        items=[_build_summary(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{slug}", response_model=RoadmapRead)
async def get_roadmap(slug: str, db: AsyncSession = Depends(get_db)):
    rm = await crud.get_roadmap_by_slug(db, slug)
    if not rm:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return _build_read(rm)
