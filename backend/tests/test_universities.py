from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.university import University
from app.models.course import Course, CourseLevel


@pytest_asyncio.fixture
async def sample_university(db_session: AsyncSession) -> University:
    uni = University(
        name="Test University",
        slug="test-university",
        source_key="test",
        country="US",
    )
    db_session.add(uni)
    await db_session.commit()
    await db_session.refresh(uni)
    return uni


@pytest_asyncio.fixture
async def sample_course(db_session: AsyncSession, sample_university: University) -> Course:
    course = Course(
        university_id=sample_university.id,
        title="Introduction to Testing",
        slug="intro-to-testing-test-university",
        level=CourseLevel.undergraduate,
        source_key="test",
        has_video_lectures=True,
        total_videos=10,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


# ─── University endpoints ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_universities_empty(client: AsyncClient):
    resp = await client.get("/api/v1/universities")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert isinstance(body["items"], list)
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_list_universities_with_data(
    client: AsyncClient, sample_university: University
):
    resp = await client.get("/api/v1/universities")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    slugs = [u["slug"] for u in body["items"]]
    assert "test-university" in slugs


@pytest.mark.asyncio
async def test_get_university_by_slug(
    client: AsyncClient, sample_university: University
):
    resp = await client.get("/api/v1/universities/test-university")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test University"


@pytest.mark.asyncio
async def test_get_university_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/universities/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_university_courses(
    client: AsyncClient, sample_course: Course, sample_university: University
):
    resp = await client.get(f"/api/v1/universities/{sample_university.slug}/courses")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert body["items"][0]["title"] == "Introduction to Testing"
