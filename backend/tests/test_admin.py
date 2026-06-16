from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.university import University
from app.models.course import Course, CourseLevel


@pytest.mark.asyncio
async def test_admin_login_success(auth_client: AsyncClient):
    # auth_client already has a valid token; verify a protected endpoint works
    resp = await auth_client.get("/api/v1/admin/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert "total_universities" in body
    assert "total_courses" in body


@pytest.mark.asyncio
async def test_admin_login_fail(client: AsyncClient):
    resp = await client.post(
        "/api/v1/admin/auth/login",
        json={"email": "bad@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_login_uses_httponly_cookie(
    client: AsyncClient, db_session: AsyncSession
):
    from app.config import settings
    from app.services.auth import get_or_create_admin

    await get_or_create_admin(db_session)
    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )

    assert response.status_code == 200, response.text
    assert "httponly" in response.headers["set-cookie"].lower()

    stats = await client.get("/api/v1/admin/stats")
    assert stats.status_code == 200

    logout = await client.post("/api/v1/admin/auth/logout")
    assert logout.status_code == 200
    assert "ocw_session=" in logout.headers["set-cookie"].lower()


@pytest.mark.asyncio
async def test_admin_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/admin/stats")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_create_university(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/v1/admin/universities",
        json={
            "name": "Harvard University",
            "slug": "harvard",
            "source_key": "harvard",
            "country": "US",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["slug"] == "harvard"


@pytest.mark.asyncio
async def test_admin_create_university_duplicate_slug(auth_client: AsyncClient):
    payload = {"name": "X", "slug": "duplicate-slug", "source_key": "x"}
    await auth_client.post("/api/v1/admin/universities", json=payload)
    resp = await auth_client.post("/api/v1/admin/universities", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_admin_stats_counts(auth_client: AsyncClient, db_session: AsyncSession):
    uni = University(name="Stats Uni", slug="stats-uni", source_key="test")
    db_session.add(uni)
    await db_session.commit()
    await db_session.refresh(uni)

    course = Course(
        university_id=uni.id,
        title="Stats Course",
        slug="stats-course-stats-uni",
        level=CourseLevel.undergraduate,
        source_key="test",
        has_video_lectures=True,
    )
    db_session.add(course)
    await db_session.commit()

    resp = await auth_client.get("/api/v1/admin/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_universities"] >= 1
    assert body["total_courses"] >= 1
    assert body["courses_with_video"] >= 1


@pytest.mark.asyncio
async def test_admin_publish_changes_only_publication_state(
    auth_client: AsyncClient, db_session: AsyncSession
):
    uni = University(name="Publish Uni", slug="publish-uni", source_key="test")
    db_session.add(uni)
    await db_session.flush()
    course = Course(
        university_id=uni.id,
        title="Preserved Course",
        slug="preserved-course",
        level=CourseLevel.undergraduate,
        source_key="test",
        description="Must remain unchanged",
        is_published=False,
    )
    db_session.add(course)
    await db_session.commit()

    resp = await auth_client.patch(
        f"/api/v1/admin/courses/{course.id}/publish?published=true"
    )

    assert resp.status_code == 200
    assert resp.json()["is_published"] is True
    await db_session.refresh(course)
    assert course.is_published is True
    assert course.description == "Must remain unchanged"

    resp = await auth_client.patch(
        f"/api/v1/admin/courses/{course.id}/publish?published=false"
    )
    assert resp.status_code == 200
    assert resp.json()["is_published"] is False
