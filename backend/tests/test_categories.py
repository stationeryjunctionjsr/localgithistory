import pytest
from httpx import AsyncClient
from app.main import app
from app.utils.auth import require_super_admin
from app.repositories.category_repository import CategoryRepository

category_repository = CategoryRepository()


@pytest.fixture(autouse=True)
def override_admin():
    app.dependency_overrides[require_super_admin] = lambda: {"role": "super_admin"}
    yield
    app.dependency_overrides.pop(require_super_admin, None)


@pytest.mark.asyncio
async def test_category_crud_workflow(client: AsyncClient):
    # Pre-test cleanup: delete category if it already exists
    existing_all = await category_repository.storage.findAll({"name": "Test Category Returnable"})
    for e in existing_all:
        await category_repository.storage.delete(e.id)

    # 1. Create Category
    payload = {
        "name": "Test Category Returnable",
        "description": "Category for testing return feature",
        "minimumQuantity": 5,
        "gst": 12.5,
        "isReturnable": True,
    }
    response = await client.post("/api/categories/", json=payload)
    assert response.status_code in (200, 201), response.text
    created = response.json()
    assert created["name"] == "Test Category Returnable"
    assert created["gst"] == 12.5
    assert created["isReturnable"] is True
    category_id = created.get("id", created.get("_id"))

    # 2. Get Category by ID
    response = await client.get(f"/api/categories/{category_id}")
    assert response.status_code == 200
    fetched = response.json()
    assert fetched["gst"] == 12.5
    assert fetched["isReturnable"] is True

    # 3. Update Category (isReturnable -> False, gst -> 18.0)
    update_payload = {"gst": 18.0, "isReturnable": False}
    response = await client.put(f"/api/categories/{category_id}", json=update_payload)
    assert response.status_code == 200
    updated = response.json()
    assert updated["gst"] == 18.0
    assert updated["isReturnable"] is False

    # 4. Get Public Categories and verify fields exist
    response = await client.get("/api/categories/public")
    assert response.status_code == 200
    public_list = response.json()
    matched_cat = next((c for c in public_list if c.get("id", c.get("_id")) == category_id), None)
    assert matched_cat is not None
    assert matched_cat["gst"] == 18.0
    assert matched_cat["isReturnable"] is False

    # 5. Clean up
    response = await client.delete(f"/api/categories/{category_id}")
    assert response.status_code == 200




