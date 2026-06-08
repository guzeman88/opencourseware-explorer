import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_exposes_deployment_fingerprint(client: AsyncClient, monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc123")
    monkeypatch.setenv("RENDER_GIT_BRANCH", "main")

    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "1.0.0",
        "git_commit": "abc123",
        "git_branch": "main",
    }
