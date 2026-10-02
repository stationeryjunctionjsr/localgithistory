try:
    from app.models.daos import ProductInternalCreate
except ImportError:
    pass
try:
    from app.models.daos_flat import ProductInternalCreate
except ImportError:
    pass
try:
    from app.models.daos import BundleInternalCreate
except ImportError:
    pass
try:
    from app.models.daos_flat import BundleInternalCreate
except ImportError:
    pass
import pytest
from httpx import AsyncClient
from app.repositories.product_repository import product_repository
from app.repositories.bundle_repository import bundle_repository
from app.repositories.cart_repository import cart_repository


@pytest.mark.asyncio
async def test_bundle_product_recommendations(client: AsyncClient, user_auth: dict):
    # 1. Create test products
    p1 = await product_repository.create(
        ProductInternalCreate(name="Test Pen", mrp=10.0, price=8.0, stock=100, isActive=True, category="Stationery")
    )

    p2 = await product_repository.create(
        ProductInternalCreate(name="Test Notebook", mrp=50.0, price=40.0, stock=100, isActive=True, category="Stationery")
    )

    pid1 = p1.id
    pid2 = p2.id

    # 2. Create active bundles with different salesCount values
    b1 = await bundle_repository.create(
        BundleInternalCreate(**{
            "name": "Low Volume Bundle",
            "price": 50.0,
            "isActive": True,
            "products": [{"productId": pid1, "quantity": 1}, {"productId": pid2, "quantity": 1}],
            "salesCount": 5,
        })
    )

    b2 = await bundle_repository.create(
        BundleInternalCreate(**{
            "name": "High Volume Bundle",
            "price": 45.0,
            "isActive": True,
            "products": [{"productId": pid1, "quantity": 2}],
            "salesCount": 20,
        })
    )

    # 3. Retrieve bundles containing pid1 and assert descending sort by salesCount
    response = await client.get(f"/api/bundles/product/{pid1}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    bundles = data
    print(f"b1: {b1}")
    print(f"b2: {b2}")
    print(f"bundles: {bundles}")
    assert len(bundles) == 2, data

    # Highest salesCount first (High Volume Bundle has 20, Low Volume Bundle has 5)
    assert bundles[0]["name"] == "High Volume Bundle"
    assert bundles[0]["salesCount"] == 20
    assert bundles[1]["name"] == "Low Volume Bundle"
    assert bundles[1]["salesCount"] == 5

    # 4. Cleanup
    await product_repository.storage.delete(pid1)
    await product_repository.storage.delete(pid2)
    await bundle_repository.storage.delete(b1.id)
    await bundle_repository.storage.delete(b2.id)


@pytest.mark.asyncio
async def test_bundle_purchase_increments_sales_count(client: AsyncClient, user_auth: dict):
    # 1. Create a product and a bundle
    p = await product_repository.create(
        ProductInternalCreate(name="Test Item", mrp=20.0, price=15.0, stock=50, isActive=True, category="Stationery")
    )
    pid = p.id

    b = await bundle_repository.create(
        BundleInternalCreate(**{
            "name": "Test Order Bundle",
            "price": 12.0,
            "isActive": True,
            "products": [{"productId": pid, "quantity": 1}],
            "salesCount": 10,
        })
    )
    bid = b.id

    # 2. Add bundle to the user's cart (API handles tagging it with bundleId/bundleName)
    add_response = await client.post(f"/api/bundles/{bid}/add-to-cart", headers=user_auth)
    assert add_response.status_code == 200

    # 3. Place order
    order_data = {
        "shippingAddress": {
            "street": "123 Test St",
            "city": "Testville",
            "state": "TestState",
            "zipCode": "831001",
            "phone": "9999999999",
        },
        "paymentMethod": "cod",
    }
    from unittest.mock import patch
    with patch("app.repositories.feature_flag_repository.FeatureFlagRepository.is_enabled", return_value=True):
        order_response = await client.post("/api/orders/", json=order_data, headers=user_auth)
    assert order_response.status_code == 201, order_response.text
    order_id = order_response.json().get("_id", order_response.json().get("id"))

    # 4. Fetch the bundle again and verify salesCount incremented to 11
    updated_bundle = await bundle_repository.findById(bid)
    assert updated_bundle.sales_count == 11

    # 5. Cleanup
    if order_id:
        from app.repositories.order_repository import order_repository

        await order_repository.storage.delete(str(order_id))
    await bundle_repository.storage.delete(bid)
    await product_repository.storage.delete(pid)