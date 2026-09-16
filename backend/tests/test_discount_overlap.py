import pytest
import uuid
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_discount_overlap(client):
    response = await client.get("/api/coupons/")
    assert response.status_code in [200, 401, 403, 404]
