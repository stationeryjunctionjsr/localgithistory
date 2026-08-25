"""Health and readiness endpoint tests.

These run quickly with no auth required and should always pass in CI.
Fixtures (client) come from conftest.py.
"""

import pytest


@pytest.mark.asyncio
async def test_health_ok(client):
    """Health endpoint responds 200 or 503 (never 500) and has expected keys."""
    response = await client.get("/api/health")
    assert response.status_code in (200, 503), (
        f"Health endpoint should return 200 or 503 (not 5xx crash), got {response.status_code}"
    )
    data = response.json()
    assert "status" in data, "Health response must contain 'status' key"


@pytest.mark.asyncio
async def test_version_endpoint(client):
    """Version endpoint returns 200 with a version string."""
    response = await client.get("/api/app/version")
    assert response.status_code == 200, f"Expected 200 for /api/app/version, got {response.status_code}"
    data = response.json()
    assert "current" in data, "Version response must contain 'current' key"
    assert isinstance(data["current"], str), "Version must be a string"


@pytest.mark.asyncio
async def test_docs_accessible(client):
    """OpenAPI docs endpoint should be reachable in non-production."""
    response = await client.get("/docs")
    assert response.status_code in (200, 404), (
        f"Docs should return 200 (or 404 in production), got {response.status_code}"
    )


@pytest.mark.asyncio
async def test_metrics_accessible(client):
    """/metrics endpoint should respond (Prometheus scrape target)."""
    response = await client.get("/metrics")
    assert response.status_code in (200, 404), (
        f"Metrics should return 200 (or 404 if disabled), got {response.status_code}"
    )
