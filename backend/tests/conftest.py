from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models import Base

# Each test gets its own in-memory SQLite DB (unique URL per test)
_db_counter = 0


def _next_db_url() -> str:
    global _db_counter
    _db_counter += 1
    # shared cache allows same in-memory DB across connections
    return f"sqlite+aiosqlite:///file:testdb_{_db_counter}?mode=memory&cache=shared&uri=true"


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture
async def db_session(monkeypatch) -> AsyncGenerator[AsyncSession, None]:
    """Fresh in-memory SQLite DB for every test function."""
    from app.config import settings

    monkeypatch.setattr(settings, "admin_email", "admin@example.com")
    monkeypatch.setattr(settings, "admin_password", "changeme")

    engine = create_async_engine(_next_db_url(), echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    from app.models.course import Course
    from app.routers import courses as courses_router

    async def increment_view_in_test_db(course_id):
        course = await db_session.get(Course, course_id)
        if course is not None:
            course.view_count += 1
            await db_session.commit()

    monkeypatch.setattr(
        courses_router,
        "_increment_view_background",
        increment_view_in_test_db,
    )

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(db_session: AsyncSession, monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    """Client pre-authenticated as admin."""
    from app.services.auth import get_or_create_admin, create_access_token
    from app.models.course import Course
    from app.routers import courses as courses_router

    async def increment_view_in_test_db(course_id):
        course = await db_session.get(Course, course_id)
        if course is not None:
            course.view_count += 1
            await db_session.commit()

    monkeypatch.setattr(
        courses_router,
        "_increment_view_background",
        increment_view_in_test_db,
    )

    admin = await get_or_create_admin(db_session)
    token = create_access_token({"sub": admin.email})

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
