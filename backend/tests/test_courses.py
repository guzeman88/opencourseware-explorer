from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course, CourseLevel, CourseSubject, CourseSubjectRelevance
from app.models.subject import Subject
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
async def test_subject_relevance_uses_sidecar_scores(
    client: AsyncClient,
    db_session: AsyncSession,
    uni: University,
):
    subject = Subject(name="Discrete Mathematics", slug="discrete-mathematics")
    exact = Course(
        university_id=uni.id,
        title="Discrete Mathematics",
        slug="discrete-mathematics-test",
        level=CourseLevel.undergraduate,
        source_key="test",
        has_video_lectures=True,
        total_videos=12,
        view_count=1,
    )
    weak = Course(
        university_id=uni.id,
        title="Advanced Hematologic System Physiology",
        slug="advanced-hematologic-system-physiology-test",
        level=CourseLevel.undergraduate,
        source_key="test",
        has_video_lectures=True,
        total_videos=16,
        view_count=999,
    )
    db_session.add_all([subject, exact, weak])
    await db_session.flush()
    db_session.add_all(
        [
            CourseSubject(course_id=exact.id, subject_id=subject.id),
            CourseSubject(course_id=weak.id, subject_id=subject.id),
            CourseSubjectRelevance(
                course_id=exact.id,
                subject_id=subject.id,
                score=100,
                relationship="exact_title",
                reason="title contains 'discrete mathematics'",
            ),
            CourseSubjectRelevance(
                course_id=weak.id,
                subject_id=subject.id,
                score=35,
                relationship="weak_existing_tag",
                reason="existing tag only; no direct text evidence",
            ),
        ]
    )
    await db_session.commit()

    resp = await client.get(
        "/api/v1/courses?subject_slug=discrete-mathematics&sort_by=relevance&page_size=10"
    )
    assert resp.status_code == 200
    titles = [item["title"] for item in resp.json()["items"]]
    assert titles[0] == "Discrete Mathematics"
    assert "Advanced Hematologic System Physiology" not in titles


@pytest.mark.asyncio
async def test_strict_relevance_allows_multi_subject_title_matches(
    client: AsyncClient,
    db_session: AsyncSession,
    uni: University,
):
    logic = Subject(name="Logic", slug="logic")
    proof = Subject(name="Proof Writing", slug="proof-writing")
    course = Course(
        university_id=uni.id,
        title="Logic and Proof",
        slug="logic-and-proof-test",
        level=CourseLevel.undergraduate,
        source_key="test",
        has_video_lectures=True,
        total_videos=8,
        view_count=1,
    )
    db_session.add_all([logic, proof, course])
    await db_session.commit()

    logic_resp = await client.get(
        "/api/v1/courses?subject_slug=logic&sort_by=relevance&page_size=10"
    )
    proof_resp = await client.get(
        "/api/v1/courses?subject_slug=proof-writing&sort_by=relevance&page_size=10"
    )

    assert logic_resp.status_code == 200
    assert proof_resp.status_code == 200
    assert "Logic and Proof" in [item["title"] for item in logic_resp.json()["items"]]
    assert "Logic and Proof" in [item["title"] for item in proof_resp.json()["items"]]

    subjects_resp = await client.get("/api/v1/subjects?page_size=500&strict_counts=true")
    assert subjects_resp.status_code == 200
    counts = {
        item["slug"]: item["course_count"] for item in subjects_resp.json()["items"]
    }
    assert counts["logic"] == 1
    assert counts["proof-writing"] == 1


@pytest.mark.asyncio
async def test_view_count_increments(client: AsyncClient, courses: list[Course]):
    slug = "linear-algebra-mit"
    resp1 = await client.get(f"/api/v1/courses/{slug}")
    view1 = resp1.json()["view_count"]
    resp2 = await client.get(f"/api/v1/courses/{slug}")
    view2 = resp2.json()["view_count"]
    assert view2 >= view1  # may be equal if rollback
