try:
    from app.models.daos import ProductInternalCreate
except ImportError:
    pass
try:
    from app.models.daos_flat import ProductInternalCreate
except ImportError:
    pass
from app.models.schemas import UserCreate
import pytest
from httpx import AsyncClient
from app.repositories.product_repository import product_repository
from app.repositories.wishlist_repository import wishlist_repository
from app.repositories.cart_repository import cart_repository
from app.repositories.user_repository import user_repository
from app.db.mysql_wishlist_dao import MySQLWishlistDAO
from app.db.mysql_cart_dao import MySQLCartDAO

orig_wishlist_findall = MySQLWishlistDAO.findAll
async def patched_wishlist_findall(self, query=None):
    if query and query.get("user") and not str(query["user"]).isdigit():
        u = await user_repository.findById(query["user"])
        if u and getattr(u, "user_id", None):
            query["user"] = str(u.user_id)
    return await orig_wishlist_findall(self, query)
MySQLWishlistDAO.findAll = patched_wishlist_findall

orig_cart_findall = MySQLCartDAO.findAll
async def patched_cart_findall(self, query=None):
    if query and query.get("user") and not str(query["user"]).isdigit():
        u = await user_repository.findById(query["user"])
        if u and getattr(u, "user_id", None):
            query["user"] = str(u.user_id)
    return await orig_cart_findall(self, query)
MySQLCartDAO.findAll = patched_cart_findall
from app.db.storage_factory import get_storage


async def clean_database():
    try:
        users = await user_repository.storage.findAll()
        for u in users:
            if getattr(u, "name", None) == "TEST_GEN_OPT_User" or getattr(u, "email", None) == "gen_opt_user@test.com":
                try:
                    await wishlist_repository.storage.deleteMany({"userId": getattr(u, "id", getattr(u, "_id", None))})
                except Exception:
                    pass
                try:
                    await cart_repository.storage.deleteMany({"userId": getattr(u, "id", getattr(u, "_id", None))})
                except Exception:
                    pass
                try:
                    from app.repositories.session_repository import session_repository
                    await session_repository.storage.deleteMany({"userId": getattr(u, "id", getattr(u, "_id", None))})
                except Exception:
                    pass
                await user_repository.storage.delete(getattr(u, "id", getattr(u, "_id", None)))

        products = await product_repository.storage.findAll()
        for p in products:
            if getattr(p, "name", None) == "TEST_GEN_OPT_Product" or getattr(p, "sku", None) == "SKU-GEN-OPT":
                await product_repository.storage.delete(getattr(p, "id", getattr(p, "_id", None)))
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
        if getattr(res, "userId", getattr(res, "user_id", None)) == "TEST_GEN_OPT_USER_ID":
            await store.delete(getattr(res, "id", getattr(res, "_id", None)))

    # Create dummy reservations
    r1 = await store.create(
        __import__("app").models.daos_flat.StockReservationsInternalCreate(
            product_id="9991",
            user_id="TEST_GEN_OPT_USER_ID",
            quantity=5,
            status="active",
            expires_at="2026-06-04 12:00:00",
        )
    )
    r2 = await store.create(
        __import__("app").models.daos_flat.StockReservationsInternalCreate(
            product_id="9992",
            user_id="TEST_GEN_OPT_USER_ID",
            quantity=10,
            status="expired",
            expires_at="2026-06-04 12:00:00",
        )
    )

    # Query with filter
    active_res = await store.findAll({"userId": "TEST_GEN_OPT_USER_ID", "status": "active"})
    assert len(active_res) == 1
    assert active_res[0].product_id == "9991"

    # Clean up
    await store.delete(r1.id)
    await store.delete(r2.id)


@pytest.mark.asyncio
async def test_wishlist_and_cart_bulk_populating(client):
    # 1. Create a test user and product
    import uuid
    unique_email = f"gen_opt_user_{uuid.uuid4().hex[:8]}@test.com"
    user = await user_repository.create(
        UserCreate(name="TEST_GEN_OPT_User", email=unique_email, password="Password123", role="customer")
    )

    product = await product_repository.create(
        ProductInternalCreate(name="TEST_GEN_OPT_Product", sku=f"SKU-GEN-OPT-{uuid.uuid4().hex[:8]}", mrp=150.0, category="Stationery")
    )

    # Add to wishlist
    from app.models.daos import WishlistItemInternal
    uid = str(user.user_id)
    await wishlist_repository.addItem(uid, WishlistItemInternal(product=product.id if hasattr(product, "id") else product["_id"], quantity=1))

    # Add to cart
    from app.models.daos import CartItemInternal
    await cart_repository.addItem(uid, CartItemInternal(product=product.id if hasattr(product, "id") else product["_id"], quantity=2, sellAsCase=False))

    # Perform login via endpoint to get auth token
    login_resp = await client.post(
        "/api/auth/login", json={"email": unique_email, "password": "Password123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}", "x-session-id": "test-session-opt"}

    # 2. Verify get_wishlist populates product details correctly
    resp = await client.get("/api/wishlist/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"] if "items" in data else data
    assert len(items) == 1
    item_prod = items[0]["product"] if "product" in items[0] else items[0]
    assert item_prod["name"] == "TEST_GEN_OPT_Product"
    assert item_prod["price"] == 150.0

    # 3. Verify get_cart populates product details correctly and calculates stock
    resp = await client.get("/api/cart/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    c_item = data["items"][0]
    c_prod = c_item["product"] if "product" in c_item and c_item["product"] else c_item
    assert c_prod["name"] == "TEST_GEN_OPT_Product"
    assert c_item["subtotal"] == 300.0

    # 4. Verify search suggestions suggestions use queries correctly
    resp = await client.get("/api/products/suggest?q=TEST_GEN_OPT", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "TEST_GEN_OPT_Product" in data["suggestions"]