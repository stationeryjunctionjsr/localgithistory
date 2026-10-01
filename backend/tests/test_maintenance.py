"""Maintenance / scheduled upgrade mode tests."""

import pytest

from app.config.settings import settings


@pytest.mark.asyncio
async def test_maintenance_status_inactive_by_default(client):
    response = await client.get("/api/app/maintenance")
    assert response.status_code == 200
    data = response.json()
    assert data["active"] is False
    assert isinstance(data["message"], list)
    assert len(data["message"]) >= 1


@pytest.mark.asyncio
async def test_health_reachable_during_maintenance(client, monkeypatch):
    monkeypatch.setattr(settings, "maintenance_mode", True)

    health = await client.get("/api/health/live")
    assert health.status_code == 200

    status = await client.get("/api/app/maintenance")
    assert status.status_code == 200
    assert status.json()["active"] is True

    blocked = await client.get("/api/products")
    assert blocked.status_code == 503
    body = blocked.json()
    assert body.get("code") == "MAINTENANCE_MODE"
    assert body.get("maintenance") is True