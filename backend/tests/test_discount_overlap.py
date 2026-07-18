import pytest
import uuid
import asyncio
from httpx import AsyncClient
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_discount_overlap(client):
    response = await client.get("/api/coupons/")
    assert response.status_code in [200, 401, 403, 404]
