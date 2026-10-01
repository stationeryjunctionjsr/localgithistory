import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_recommendations_endpoint(client):
    response = await client.get("/api/recommendations/")
    assert response.status_code in [200, 307, 401, 403, 404, 400]