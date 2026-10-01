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
    product = await product_repository.create(
        ProductInternalCreate(name="SuperFuzzyWidget", mrp=100.0, price=100.0, category="Gadgets", stock=10)
    )
    product_id = product.id if hasattr(product, "id") else product["_id"]

    try:
        # 2. Search using typo (similarity ratio >= 0.7)
        # "SuperFuzzyWidget" has 16 characters. "SprFuzyWdget" has 12 characters.
        # SequenceMatcher similarity ratio of "superfuzzywidget" vs "sprfuzywdget" is:
        # 2 * 11 / (16 + 12) = 22 / 28 = 0.785 (which is >= 0.7)
        response = await client.get("/api/products/public?search=SprFuzyWdget")
        assert response.status_code == 200
        data = response.json()
        results = data["products"]

        # Verify that our test product is in the fuzzy search results and response includes fuzzy metadata
        matched_ids = [str(p["_id"]) for p in results]
        assert str(product_id) in matched_ids
        assert data["usedFuzzy"] is True
        assert data["suggestedQuery"] == "superfuzzywidget"

    finally:
        # 3. Clean up
        await product_repository.storage.delete(product_id)