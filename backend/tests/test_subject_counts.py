from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog_eligibility import SubjectCatalogCount
from app.models.subject import Subject
from app.subject_counts import STRICT_COUNT_POLICY_VERSION


@pytest.mark.asyncio
async def test_strict_subject_counts_use_persisted_sidecar(
    client: AsyncClient, db_session: AsyncSession
):
    subject = Subject(name="Discrete Mathematics", slug="discrete-mathematics")
    db_session.add(subject)
    await db_session.flush()
    db_session.add(
        SubjectCatalogCount(
            subject_id=subject.id,
            course_count=7,
            policy_version=STRICT_COUNT_POLICY_VERSION,
        )
    )
    await db_session.commit()

    response = await client.get("/api/v1/subjects?page_size=500&strict_counts=true")

    assert response.status_code == 200
    counts = {item["slug"]: item["course_count"] for item in response.json()["items"]}
    assert counts["discrete-mathematics"] == 7
