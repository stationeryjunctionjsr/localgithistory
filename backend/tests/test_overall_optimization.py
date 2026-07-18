import pytest
from httpx import AsyncClient
from app.repositories.product_repository import product_repository
from app.repositories.wishlist_repository import wishlist_repository
from app.repositories.cart_repository import cart_repository
from app.repositories.user_repository import user_repository
from app.db.storage_factory import get_storage

async def clean_database():
    try:
        # Delete test user's wishlist, cart and sessions first to satisfy foreign key constraints
        users = await user_repository.storage.findAll()
        for u in users:
            if u.get("name") == "TEST_GEN_OPT_User" or u.get("email") == "gen_opt_user@test.com":
                await wishlist_repository.storage.deleteMany({"user": u["_id"]})
                await cart_repository.storage.deleteMany({"user": u["_id"]})
                from app.repositories.session_repository import session_repository
                await session_repository.storage.deleteMany({"user": u["_id"]})
                await user_repository.storage.delete(u["_id"])

        # Delete test product
        products = await product_repository.storage.findAll()
        for p in products:
            if p.get("name") == "TEST_GEN_OPT_Product" or p.get("sku") == "SKU-GEN-OPT":
                await product_repository.storage.delete(p["_id"])
    except Exception as e:
        print(f"CLEANUP ERROR: {e}")

@pytest.fixture(autouse=True)
async def cleanup_database():
    await clean_database()
    yield
    await clean_database()

@pytest.mark.asyncio
async def test_oracle_doc_store_filtering():
    # Test JSON_VALUE query filtering on DocStore
    store = get_storage("stockReservations")
    
    # Clean up test reservations first
    all_res = await store.findAll()
    for res in all_res:
        if res.get("userId") == "TEST_GEN_OPT_USER_ID":
            await store.delete(res["_id"])

    # Create dummy reservations
    r1 = await store.create({
        "productId": "9991",
        "userId": "TEST_GEN_OPT_USER_ID",
        "quantity": 5,
        "status": "active",
        "expiresAt": "2026-06-04T12:00:00Z"
    })
    r2 = await store.create({
        "productId": "9992",
        "userId": "TEST_GEN_OPT_USER_ID",
        "quantity": 10,
        "status": "expired",
        "expiresAt": "2026-06-04T12:00:00Z"
    })

    # Query with filter
    active_res = await store.findAll({"userId": "TEST_GEN_OPT_USER_ID", "status": "active"})
    assert len(active_res) == 1
    assert active_res[0]["productId"] == "9991"

    # Clean up
    await store.delete(r1["_id"])
    await store.delete(r2["_id"])

@pytest.mark.asyncio
async def test_wishlist_and_cart_bulk_populating(client):
    # 1. Create a test user and product
    user = await user_repository.create({
        "name": "TEST_GEN_OPT_User",
        "email": "gen_opt_user@test.com",
        "password": "Password123",
        "role": "customer"
    })
    
    product = await product_repository.create({
        "name": "TEST_GEN_OPT_Product",
        "sku": "SKU-GEN-OPT",
        "mrp": 150.0,
        "category": "Stationery"
    })

    # Add to wishlist
    await wishlist_repository.addItem(user["_id"], {"product": product["_id"], "quantity": 1})

    # Add to cart
    await cart_repository.addItem(user["_id"], {
        "product": product["_id"],
        "quantity": 2,
        "sellAsCase": False
    })

    # Perform login via endpoint to get auth token
    login_resp = await client.post("/api/auth/login", json={
        "email": "gen_opt_user@test.com",
        "password": "Password123"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}", "x-session-id": "test-session-opt"}

    # 2. Verify get_wishlist populates product details correctly
    resp = await client.get("/api/wishlist/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product"]["name"] == "TEST_GEN_OPT_Product"
    assert data["items"][0]["product"]["price"] == 150.0

    # 3. Verify get_cart populates product details correctly and calculates stock
    resp = await client.get("/api/cart/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product"]["name"] == "TEST_GEN_OPT_Product"
    assert data["items"][0]["subtotal"] == 300.0

    # 4. Verify search suggestions suggestions use queries correctly
    resp = await client.get("/api/products/suggest?q=TEST_GEN_OPT", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "TEST_GEN_OPT_Product" in data["suggestions"]
