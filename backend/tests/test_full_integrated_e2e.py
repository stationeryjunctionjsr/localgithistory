import pytest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.schemas import UserCreate
from app.repositories.user_repository import user_repository
from app.repositories.feature_flag_repository import FeatureFlagRepository

@pytest.mark.asyncio
async def test_full_integrated_e2e():
    from app.models.feature_flag import FeatureFlag
    feature_flag_repository = FeatureFlagRepository()
    existing = await feature_flag_repository.find_by_flag_id("retail_enable_cod")
    if existing:
        existing.enabled = "true"
        await feature_flag_repository.update(existing.id, existing)
    else:
        await feature_flag_repository.create(FeatureFlag(id="retail_enable_cod", name="COD", enabled="true"))
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@test.com"
    seller_email = f"seller_{uuid.uuid4().hex[:8]}@test.com"
    customer_email = f"customer_{uuid.uuid4().hex[:8]}@test.com"

    # 1. Create Users via repository
    admin = await user_repository.create(UserCreate(name="Admin", email=admin_email, password="pass", role="super_admin"))
    await asyncio.sleep(0.5)
    seller = await user_repository.create(UserCreate(name="Seller", email=seller_email, password="pass", role="seller", isSellerAdmin=True, commissionOverridePct=10.0))
    await asyncio.sleep(0.5)
    customer = await user_repository.create(UserCreate(name="Customer", email=customer_email, password="pass", role="customer"))
    await asyncio.sleep(0.5)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async def login(email):
            r = await client.post("/api/auth/login", json={"email": email, "password": "pass"})
            return {"Authorization": f"Bearer {r.json()['token']}"}

        admin_auth = await login(admin_email)
        seller_auth = await login(seller_email)
        cust_auth = await login(customer_email)

        # 2. Create Category & Product via API
        cat_payload = {"name": f"Test Category {uuid.uuid4().hex[:4]}", "isActive": True, "commissionPercentage": 5.0}
        res = await client.post("/api/categories/", json=cat_payload, headers=admin_auth)
        assert res.status_code in [200, 201], res.text
        cat_id = res.json()["_id"] if "_id" in res.json() else res.json()["id"]
        
        prod_payload = {
            "name": f"Test Prod {uuid.uuid4().hex[:4]}",
            "categoryId": str(cat_id), "category": cat_payload["name"], "mrp": 1200.0,
            "sellers": [{"sellerId": str(seller.id), "stock": 10}],
            "price": 1000.0,
            "stock": 10,
            "isActive": True,
            "isApproved": True,
            "pincodes": ["123456"],
            "unit": "pcs",
            "isGstCharged": True,
            "gstPercent": 18,
            "images": ["http://test/img"]
        }
        res = await client.post("/api/products/", json=prod_payload, headers=admin_auth)
        assert res.status_code in [200, 201], res.text
        prod_id = res.json()["_id"] if "_id" in res.json() else res.json()["id"]

        # 3. Create a Coupon (Flat 100 off) via API
        coupon_payload = dict(
            code=f"FLAT100_{uuid.uuid4().hex[:4]}".upper(),
            description="Flat 100 Off",
            discountType="fixed",
            discountValue=100.0,
            minOrderValue=500.0,
            isActive=True,
            validFrom="2024-01-01T00:00:00Z",
            validUntil="2030-01-01T00:00:00Z",
            usageLimit=10
        )
        res = await client.post("/api/coupons/?force=true", json=coupon_payload, headers=admin_auth)
        assert res.status_code in [200, 201], res.text
        coupon = res.json()

        # 4. Add to Wishlist
        # wishlist_payload = {"items": [{"productId": str(prod_id)}]}
        # res = await client.post("/api/wishlist/", json=wishlist_payload, headers=cust_auth)
        # assert res.status_code in [200, 201], res.text

        # 5. Add to Cart
        cart_payload = {"productId": str(prod_id), "quantity": 1}
        res = await client.post("/api/cart/", json=cart_payload, headers=cust_auth)
        assert res.status_code in [200, 201], res.text
        
        # 7. Order Creation (Checkout)
        order_payload = {
            "paymentMethod": "cod",
            "shippingAddress": {
                "street": "123 Main St",
                "city": "Test City",
                "state": "Test State",
                "zipCode": "123456",
                "country": "Test Country",
                "phone": "9999999999"
            },
            "billingAddress": {
                "street": "123 Main St",
                "city": "Test City",
                "state": "Test State",
                "zipCode": "123456",
                "country": "Test Country",
                "phone": "9999999999"
            },
            "couponCode": coupon["code"],
            "items": [{"productId": str(prod_id), "quantity": 1, "sellAsCase": False}]
        }
        res = await client.post("/api/orders/", json=order_payload, headers=cust_auth)
        assert res.status_code in [200, 201], res.text
        order_data = res.json()
        order_id = order_data["_id"] if "_id" in order_data else order_data.get("id")
        
        # 8. Delivery Flow
        # Find sub-order ID
        res = await client.get("/api/orders/seller-orders", headers=seller_auth)
        if len(res.json()["subOrders"]) == 0:
            print("ORDER CREATED: ", order_data)
            all_so = await client.get("/api/orders/admin/sub-orders", headers=admin_auth)
            print("ALL SUB ORDERS IN SYSTEM: ", all_so.json())

        assert res.status_code in [200, 201]
        my_orders = res.json()["subOrders"]
        sub_order_id = my_orders[0].get("id") or my_orders[0].get("_id")
        
        # Mark delivered
        res = await client.put(f"/api/orders/seller-orders/{sub_order_id}/status", json={"status": "delivered"}, headers=seller_auth)
        assert res.status_code in [200, 201], res.text
        
        await asyncio.sleep(2)
        # Reduce return window to 0
        await client.put("/api/settings/returns", json={"returnDays": 0}, headers=admin_auth)
        await client.post("/api/commission/realize-pending", headers=admin_auth)
        # 9. Seller Payout
        res = await client.post(f"/api/seller-payouts/settle-all/{seller.id}", headers=admin_auth)
        assert res.status_code in [200, 201], res.text
        payout = res.json()

        print("--------------------------------------------------")
        print(f"Order created: {order_id}, Total: {order_data.get('total')}, Discount: {order_data.get('discount')}")
        print(f"Seller payout created: {payout.get('id', payout.get('_id'))}, Amount Settled: {payout['amount']}")
        print("--------------------------------------------------")













