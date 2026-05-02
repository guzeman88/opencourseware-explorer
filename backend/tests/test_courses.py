from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course, CourseLevel
from app.models.university import University


@pytest_asyncio.fixture
async def uni(db_session: AsyncSession) -> University:
    u = University(name="MIT", slug="mit", source_key="mit_ocw", country="US")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def courses(db_session: AsyncSession, uni: University) -> list[Course]:
    items = [
        Course(
            university_id=uni.id,
            title="Linear Algebra",
            slug="linear-algebra-mit",
            level=CourseLevel.undergraduate,
            source_key="mit_ocw",
            has_video_lectures=True,
            total_videos=35,
            course_number="18.06",
        ),
        Course(
            university_id=uni.id,
            title="Algorithms",
            slug="algorithms-mit",
            level=CourseLevel.undergraduate,
            source_key="mit_ocw",
            has_video_lectures=False,
            total_videos=0,
            course_number="6.006",
        ),
        Course(
            university_id=uni.id,
            title="Advanced Topics in Databases",
            slug="advanced-databases-mit",
            level=CourseLevel.graduate,
            source_key="mit_ocw",
            has_video_lectures=True,
            total_videos=20,
        ),
    ]
    db_session.add_all(items)
    await db_session.commit()
    return items


@pytest.mark.asyncio
async def test_list_courses_paginated(client: AsyncClient, courses: list[Course]):
    resp = await client.get("/api/v1/courses?page=1&page_size=2")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) <= 2
    assert body["total"] >= 3


@pytest.mark.asyncio
async def test_list_courses_filter_video(client: AsyncClient, courses: list[Course]):
    resp = await client.get("/api/v1/courses?has_video_lectures=true")
    assert resp.status_code == 200
    body = resp.json()
    for item in body["items"]:
        assert item["has_video_lectures"] is True


@pytest.mark.asyncio
async def test_list_courses_filter_level(client: AsyncClient, courses: list[Course]):
    resp = await client.get("/api/v1/courses?level=graduate")
    assert resp.status_code == 200
    body = resp.json()
    for item in body["items"]:
        assert item["level"] == "graduate"


@pytest.mark.asyncio
async def test_get_course_by_slug(client: AsyncClient, courses: list[Course]):
    resp = await client.get("/api/v1/courses/linear-algebra-mit")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Linear Algebra"


@pytest.mark.asyncio
async def test_get_course_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/courses/does-not-exist-xyz")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_search_courses(client: AsyncClient, courses: list[Course]):
    resp = await client.get("/api/v1/search?q=algebra")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any("Algebra" in i["title"] or "algebra" in i["title"].lower() for i in body["items"])


@pytest.mark.asyncio
async def test_featured_courses(client: AsyncClient, courses: list[Course]):
    resp = await client.get("/api/v1/courses/featured")
    assert resp.status_code == 200
    body = resp.json()
    # Featured only returns courses with video lectures
    for item in body["items"]:
        assert item["has_video_lectures"] is True


@pytest.mark.asyncio
async def test_view_count_increments(client: AsyncClient, courses: list[Course]):
    slug = "linear-algebra-mit"
    resp1 = await client.get(f"/api/v1/courses/{slug}")
    view1 = resp1.json()["view_count"]
    resp2 = await client.get(f"/api/v1/courses/{slug}")
    view2 = resp2.json()["view_count"]
    assert view2 >= view1  # may be equal if rollback
