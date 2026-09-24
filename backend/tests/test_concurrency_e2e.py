import pytest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.schemas import UserCreate
from app.repositories.user_repository import user_repository
from app.repositories.product_repository import product_repository
from app.db.storage_factory import get_storage
from app.models.daos import CategoryInternalCreate, ProductInternalCreate

@pytest.mark.asyncio
async def test_concurrent_cart_additions():
    """
    Test adding the last stock item to the cart simultaneously by 2 users.
    Only one should succeed, or if both succeed in cart, only one should checkout.
    Stock reservation should prevent the second one.
    """
    u1_email = f"user1_{uuid.uuid4().hex[:8]}@test.com"
    u2_email = f"user2_{uuid.uuid4().hex[:8]}@test.com"

    await user_repository.create(UserCreate(name="User1", email=u1_email, password="pass", role="customer"))
    await user_repository.create(UserCreate(name="User2", email=u2_email, password="pass", role="customer"))

    cat_storage = get_storage("categories")
    cat_doc = await cat_storage.create(CategoryInternalCreate(name=f"Cat_{uuid.uuid4().hex[:8]}", isActive=True, gst=18.0))
    
    prod_doc = await product_repository.create(ProductInternalCreate(
        name="Limited Product",
        mrp=100.0, price=90.0,
        category=cat_doc.name,
        stock=1,
        isActive=True
    ))
    prod_id = str(prod_doc.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async def login(email):
            r = await client.post("/api/auth/login", json={"email": email, "password": "pass"})
            return {"Authorization": f"Bearer {r.json()['token']}"}

        auth1 = await login(u1_email)
        auth2 = await login(u2_email)

        cart_payload = {"productId": prod_id, "quantity": 1}

        # Issue concurrent requests to cart
        req1 = client.post("/api/cart", json=cart_payload, headers=auth1)
        req2 = client.post("/api/cart", json=cart_payload, headers=auth2)

        results = await asyncio.gather(req1, req2, return_exceptions=True)

        statuses = [r.status_code for r in results if not isinstance(r, Exception)]
        
        # At most one should get a successful 200, the other should get a 400/409 error because stock=1
        success_count = statuses.count(200)
        assert success_count <= 1, f"Race condition! Both users were able to reserve stock in cart. Statuses: {statuses}"


@pytest.mark.asyncio
async def test_concurrent_checkout():
    """
    Test checking out the last stock item simultaneously if both bypassed cart (or used direct checkout).
    Since cart reserves stock now, maybe we can test race condition on checkout by simulating 
    stock=1, both users have it in cart somehow (e.g. they both added when stock=2, then stock was changed to 1,
    or one user tries to checkout concurrently).
    """
    u1_email = f"user3_{uuid.uuid4().hex[:8]}@test.com"
    u2_email = f"user4_{uuid.uuid4().hex[:8]}@test.com"

    await user_repository.create(UserCreate(name="User3", email=u1_email, password="pass", role="customer"))
    await user_repository.create(UserCreate(name="User4", email=u2_email, password="pass", role="customer"))

    cat_storage = get_storage("categories")
    cat_doc = await cat_storage.create(CategoryInternalCreate(name=f"Cat_{uuid.uuid4().hex[:8]}", isActive=True, gst=18.0))
    
    prod_doc = await product_repository.create(ProductInternalCreate(
        name="Checkout Product",
        mrp=100.0, price=90.0,
        category=cat_doc.name,
        stock=2, # start with 2 so both can add to cart
        isActive=True
    ))
    prod_id = str(prod_doc.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async def login(email):
            r = await client.post("/api/auth/login", json={"email": email, "password": "pass"})
            return {"Authorization": f"Bearer {r.json()['token']}"}

        auth1 = await login(u1_email)
        auth2 = await login(u2_email)

        cart_payload = {"productId": prod_id, "quantity": 1}

        await client.post("/api/cart", json=cart_payload, headers=auth1)
        await client.post("/api/cart", json=cart_payload, headers=auth2)
        
        # Now reduce stock to 1
        from app.models.daos import ProductInternalUpdate
        await product_repository.update(prod_id, ProductInternalUpdate(stock=1))

        checkout_payload = {
            "shippingAddress": {"street": "123 Test", "city": "City", "state": "ST", "pincode": "123456"},
            "paymentMethod": "cod"
        }

        # Issue concurrent requests to checkout
        req1 = client.post("/api/orders", json=checkout_payload, headers=auth1)
        req2 = client.post("/api/orders", json=checkout_payload, headers=auth2)

        results = await asyncio.gather(req1, req2, return_exceptions=True)

        statuses = [r.status_code for r in results if not isinstance(r, Exception)]
        
        success_count = statuses.count(201) + statuses.count(200)
        assert success_count <= 1, f"Race condition! Both users were able to checkout when stock was 1. Statuses: {statuses}"
