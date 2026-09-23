from datetime import datetime, timezone, timedelta
import asyncio
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.schemas import UserCreate
from app.repositories.user_repository import user_repository
from app.repositories.product_repository import product_repository
from app.repositories.category_repository import category_repository
from app.repositories.order_repository import order_repository
from app.db.storage_factory import get_storage
from app.models.daos import CategoryInternalUpdate, ProductInternalUpdate

@pytest.mark.asyncio
async def test_full_returns_e2e_flow():
    # Setup test users
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@test.com"
    seller_email = f"seller_{uuid.uuid4().hex[:8]}@test.com"
    valet_email = f"valet_{uuid.uuid4().hex[:8]}@test.com"
    customer_email = f"cust_{uuid.uuid4().hex[:8]}@test.com"

    await user_repository.create(UserCreate(name="Admin", email=admin_email, password="pass", role="super_admin"))
    await user_repository.create(UserCreate(name="Seller", email=seller_email, password="pass", role="seller"))
    valet = await user_repository.create(UserCreate(name="Valet", email=valet_email, password="pass", role="valet", isOnDuty=True, isApproved=True))
    await user_repository.create(UserCreate(name="Customer", email=customer_email, password="pass", role="customer"))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login
        async def login(email):
            r = await client.post("/api/auth/login", json={"email": email, "password": "pass"})
            return {"Authorization": f"Bearer {r.json()['token']}"}
        
        admin_auth = await login(admin_email)
        cust_auth = await login(customer_email)

        # Create Category and Product
        cat_storage = get_storage("categories")
        cat_doc = await cat_storage.create(CategoryInternalUpdate(name=f"Returns Category {uuid.uuid4().hex[:8]}", isActive=True))
        
        prod_doc = await product_repository.create(ProductInternalUpdate(
            name="Returnable Product",
            mrp=100.0,
            category=str(cat_doc.id),
            stock=10,
            isActive=True,
            isReturnable=True,
            returnDays=7
        ))
        prod_id = str(prod_doc.id)

        # Place an Order
        cart_payload = {"productId": prod_id, "quantity": 1}
        await client.post("/api/cart", json=cart_payload, headers=cust_auth)
        
        checkout_payload = {
            "address": {"street": "123 Test St", "city": "Test", "state": "TS", "pincode": "123456"},
            "paymentMethod": "cod"
        }
        res = await client.post("/api/orders", json=checkout_payload, headers=cust_auth)
        assert res.status_code in (200, 201)
        order_id = res.json()["_id"]

        # Mark order as delivered so it can be returned
        now_iso = datetime.now(timezone.utc).isoformat()
        await order_repository.update(order_id, {"status": "delivered", "delivered_at": now_iso})

        # Check Eligibility
        res = await client.get(f"/api/returns/order/{order_id}/eligibility", headers=cust_auth)
        assert res.status_code == 200, res.text
        eligibility = res.json()
        assert len(eligibility["eligibleItems"]) > 0, "No items eligible for return!"

        # Request Return
        return_payload = {
            "orderId": order_id,
            "items": [{"productId": prod_id, "quantity": 1, "price": 100.0, "returnReason": "Defective"}],
            "paymentMethod": "wallet"
        }
        res = await client.post("/api/returns/request", json=return_payload, headers=cust_auth)
        assert res.status_code == 200, f"Return request failed: {res.text}"
        return_id = res.json()["_id"]

        # Admin Auto-assigns valet
        res = await client.post(f"/api/returns/admin/{return_id}/auto-assign", headers=admin_auth)
        assert res.status_code == 200, f"Auto-assign failed: {res.text}"
        
        print("Returns E2E Flow successful!")
