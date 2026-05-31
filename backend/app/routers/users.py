import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.course import Course
from app.models.library import UserLibraryCourse
from app.models.watch_history import UserWatchHistory
from app.models.user import User
from app.schemas.course import CourseSummary
from app.schemas.user import (
    LibraryCourseId,
    LibraryStatusResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
    WatchHistoryCreate,
    WatchHistoryWithCourse,
)
from app.services.auth import (
    authenticate_user,
    create_access_token,
    hash_password,
)
from app.services.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


# ─── Auth ─────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    existing = (
        await db.execute(select(User).where(User.email == data.email))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await authenticate_user(db, data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


# ─── Library ──────────────────────────────────────────────────────────────────

@router.get("/me/library", response_model=list[CourseSummary])
async def get_library(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Course]:
    result = await db.execute(
        select(Course)
        .join(UserLibraryCourse, UserLibraryCourse.course_id == Course.id)
        .where(UserLibraryCourse.user_id == current_user.id)
        .order_by(UserLibraryCourse.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/me/library/{course_id}", response_model=LibraryStatusResponse)
async def library_status(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LibraryStatusResponse:
    entry = (
        await db.execute(
            select(UserLibraryCourse).where(
                UserLibraryCourse.user_id == current_user.id,
                UserLibraryCourse.course_id == course_id,
            )
        )
    ).scalar_one_or_none()
    return LibraryStatusResponse(saved=entry is not None)


@router.post("/me/library", response_model=LibraryStatusResponse, status_code=status.HTTP_201_CREATED)
async def add_to_library(
    body: LibraryCourseId,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LibraryStatusResponse:
    # Verify course exists
    course = (
        await db.execute(select(Course).where(Course.id == body.course_id))
    ).scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = (
        await db.execute(
            select(UserLibraryCourse).where(
                UserLibraryCourse.user_id == current_user.id,
                UserLibraryCourse.course_id == body.course_id,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            UserLibraryCourse(user_id=current_user.id, course_id=body.course_id)
        )
        await db.commit()
    return LibraryStatusResponse(saved=True)


@router.delete("/me/library/{course_id}", response_model=LibraryStatusResponse)
async def remove_from_library(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LibraryStatusResponse:
    entry = (
        await db.execute(
            select(UserLibraryCourse).where(
                UserLibraryCourse.user_id == current_user.id,
                UserLibraryCourse.course_id == course_id,
            )
        )
    ).scalar_one_or_none()
    if entry is not None:
        await db.delete(entry)
        await db.commit()
    return LibraryStatusResponse(saved=False)


# ─── Watch History ────────────────────────────────────────────────────────────

@router.post("/me/history", status_code=status.HTTP_204_NO_CONTENT)
async def record_watch(
    body: WatchHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Upsert the last-watched video index for a course."""
    existing = (
        await db.execute(
            select(UserWatchHistory).where(
                UserWatchHistory.user_id == current_user.id,
                UserWatchHistory.course_id == body.course_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.video_index = body.video_index
        from sqlalchemy import func
        existing.updated_at = func.now()
    else:
        db.add(
            UserWatchHistory(
                user_id=current_user.id,
                course_id=body.course_id,
                video_index=body.video_index,
            )
        )
    await db.commit()


@router.get("/me/history", response_model=list[WatchHistoryWithCourse])
async def get_watch_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WatchHistoryWithCourse]:
    """Return up to 20 most-recently-watched courses with course data."""
    rows = (
        await db.execute(
            select(UserWatchHistory, Course)
            .join(Course, UserWatchHistory.course_id == Course.id)
            .where(UserWatchHistory.user_id == current_user.id)
            .order_by(UserWatchHistory.updated_at.desc())
            .limit(20)
        )
    ).all()

    result = []
    for history, course in rows:
        course_summary = CourseSummary.model_validate(course)
        result.append(
            WatchHistoryWithCourse(
                course=course_summary,
                video_index=history.video_index,
                watched_at=history.updated_at,
            )
        )
    return result


@router.delete("/me/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_watch_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    rows = (
        await db.execute(
            select(UserWatchHistory).where(UserWatchHistory.user_id == current_user.id)
        )
    ).scalars().all()
    for row in rows:
        await db.delete(row)
    await db.commit()
