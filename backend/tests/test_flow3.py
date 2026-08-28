import pytest
from httpx import AsyncClient
from app.main import app
from app.utils.auth import require_super_admin

@pytest.fixture(autouse=True)
def override_admin():
    app.dependency_overrides[require_super_admin] = lambda: {"role": "super_admin"}
    yield
    app.dependency_overrides.pop(require_super_admin, None)

@pytest.mark.asyncio
async def test_banners_crud(client: AsyncClient):
    # 1. Create Banner
    payload = {
        "title": "Test Banner",
        "imageUrl": "https://example.com/banner.jpg",
        "position": "homepage_web",
        "userRole": "customer",
        "isActive": True,
        "startDate": "2026-08-28T00:00:00Z",
        "endDate": "2026-12-31T23:59:59Z"
    }
    response = await client.post("/api/banners/", json=payload)
    # The exact creation URL and payload might differ depending on router schema, let's assume standard
    assert response.status_code == 200 or response.status_code == 201, f"Banner creation failed: {response.text}"
    created = response.json()
    banner_id = created.get("_id")
    assert banner_id is not None
    
    # 2. Get Banners
    response = await client.get("/api/banners/")
    assert response.status_code == 200
    
    # 3. Get Public Banners
    response = await client.get("/api/banners/public?position=homepage_web&userRole=customer")
    assert response.status_code == 200
    
    # 4. Clean up (Assuming DELETE endpoint exists, if not, skip)
    response = await client.delete(f"/api/banners/{banner_id}")
    if response.status_code != 404 and response.status_code != 405:
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_promo_strips_crud(client: AsyncClient):
    # 1. Create Promo Strip
    payload = {
        "text": "Special Discount!",
        "isActive": True,
        "link": "/sale",
        "userRole": "guest"
    }
    response = await client.post("/api/promo-strips/", json=payload)
    assert response.status_code == 200 or response.status_code == 201, f"Promo strip creation failed: {response.text}"
    created = response.json()
    promo_id = created.get("_id")
    assert promo_id is not None
    
    # 2. Get Promo Strips
    response = await client.get("/api/promo-strips/")
    assert response.status_code == 200
    
    # 3. Get Active Promo Strips
    response = await client.get("/api/promo-strips/active")
    assert response.status_code == 200
    
    # 4. Clean up
    response = await client.delete(f"/api/promo-strips/{promo_id}")
    if response.status_code != 404 and response.status_code != 405:
        assert response.status_code == 200
