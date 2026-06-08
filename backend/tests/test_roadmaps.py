from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_roadmaps_empty_is_successful(client: AsyncClient):
    response = await client.get("/api/v1/roadmaps")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 50,
    }
