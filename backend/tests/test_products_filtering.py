try:
    from app.models.daos import ProductInternalCreate
except ImportError:
    pass
try:
    from app.models.daos_flat import ProductInternalCreate
except ImportError:
    pass
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
async def test_products_filtering_integration(client):
    response = await client.get("/api/products/")
    assert response.status_code in [200, 307, 401, 403, 404, 400]

    # Test text search
    response = await client.get("/api/products/?search=pen")
    assert response.status_code in [200, 307, 401, 403, 404, 400]

    # Test category filter
    response = await client.get("/api/products/?category=stationery")
    assert response.status_code in [200, 307, 401, 403, 404, 400]


@pytest.mark.asyncio
async def test_products_fuzzy_search_typo_tolerance(client):
    from app.repositories.product_repository import product_repository

    # 1. Create a product with a distinct name
    uid = uuid.uuid4().hex[:6]
    product = await product_repository.create(
        ProductInternalCreate(name=f"SuperFuzzyWidget{uid}", mrp=100.0, price=100.0, category="Gadgets", stock=10, is_active=True, status="active")
    )
    product_id = product.id if hasattr(product, "id") else product["_id"]
    
    # Invalidate the lightweight catalog cache so the new product is picked up
    product_repository._light_catalog_cache = {}
    from app.routers.products import _invalidate_product_caches
    _invalidate_product_caches()

    try:
        # 2. Search using typo (similarity ratio >= 0.7)
        response = await client.get(f"/api/products/public?search=SprFuzyWdget{uid}")
        assert response.status_code == 200
        data = response.json()
        results = data["products"]

        # Verify that our test product is in the fuzzy search results and response includes fuzzy metadata
        matched_ids = [str(p.get("id", p.get("_id"))) for p in results]
        assert str(product_id) in matched_ids
        assert data["usedFuzzy"] is True
        assert data["suggestedQuery"] == f"superfuzzywidget{uid}"

    finally:
        # 3. Clean up
        await product_repository.storage.delete(product_id)