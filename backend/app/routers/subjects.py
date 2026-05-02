from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import list_subjects, get_subject_by_slug
from app.database import get_db
from app.schemas.subject import SubjectList, SubjectRead

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=SubjectList)
async def list_subjects_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    top_level_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    subjects, total = await list_subjects(
        db, page=page, page_size=page_size, top_level_only=top_level_only
    )
    pages = max(1, math.ceil(total / page_size))
    items = [SubjectRead.model_validate(s) for s in subjects]
    return SubjectList(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{slug}", response_model=SubjectRead)
async def get_subject(slug: str, db: AsyncSession = Depends(get_db)):
    subj = await get_subject_by_slug(db, slug)
    if subj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return SubjectRead.model_validate(subj)
