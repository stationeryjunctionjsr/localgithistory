import pytest
import uuid
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.repositories.user_repository import user_repository
from app.models.schemas import UserCreate
from app.repositories.sub_order_repository import sub_order_repository
from app.repositories.order_repository import order_repository
from app.models.order import OrderInternalUpdate
from app.config.database import get_async_engine
from sqlalchemy import text

@pytest.mark.asyncio
async def test_multiseller_coupon_payout():
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@test.com"
    seller1_email = f"seller1_{uuid.uuid4().hex[:8]}@test.com"
    seller2_email = f"seller2_{uuid.uuid4().hex[:8]}@test.com"
    customer_email = f"customer_{uuid.uuid4().hex[:8]}@test.com"

    # Create Users
    admin = await user_repository.create(UserCreate(name="Admin", email=admin_email, password="pass", role="super_admin", isSellerAdmin=True))
    seller1 = await user_repository.create(UserCreate(name="Seller 1", email=seller1_email, password="pass", role="seller", isSellerAdmin=True))
    seller2 = await user_repository.create(UserCreate(name="Seller 2", email=seller2_email, password="pass", role="seller", isSellerAdmin=True))
    customer = await user_repository.create(UserCreate(name="Customer", email=customer_email, password="pass", role="customer"))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async def login(email):
            r = await client.post("/api/auth/login", json={"email": email, "password": "pass"})
            return {"Authorization": f"Bearer {r.json()['token']}"}

        admin_auth = await login(admin_email)
        seller1_auth = await login(seller1_email)
        seller2_auth = await login(seller2_email)
        cust_auth = await login(customer_email)

        # Create Category
        cat_payload = {"name": f"Test Category {uuid.uuid4().hex[:4]}", "isActive": True, "commissionPercentage": 10.0}
        res = await client.post("/api/categories/", json=cat_payload, headers=admin_auth)
        cat_id = res.json().get("id") or res.json().get("_id")

        # Create Product for Seller 1
        prod1_payload = {
            "name": f"Seller1 Prod {uuid.uuid4().hex[:4]}",
            "categoryId": cat_id,
            "sellers": [{"sellerId": str(seller1.id), "stock": 100}],
            "mrp": 1000.0,
            "isActive": True,
            "isApproved": True,
            "stock": 100,
            "unit": "pcs",
            "isGstCharged": False
        }
        res = await client.post("/api/products/", json=prod1_payload, headers=admin_auth)
        prod1_id = res.json().get("id") or res.json().get("_id")

        # Create Product for Seller 2
        prod2_payload = {
            "name": f"Seller2 Prod {uuid.uuid4().hex[:4]}",
            "categoryId": cat_id,
            "sellers": [{"sellerId": str(seller2.id), "stock": 100}],
            "mrp": 500.0,
            "isActive": True,
            "isApproved": True,
            "stock": 100,
            "unit": "pcs",
            "isGstCharged": False
        }
        res = await client.post("/api/products/", json=prod2_payload, headers=admin_auth)
        prod2_id = res.json().get("id") or res.json().get("_id")

        # Create Product for Super Admin (Platform)
        prod3_payload = {
            "name": f"Admin Prod {uuid.uuid4().hex[:4]}",
            "categoryId": cat_id,
            "sellers": [{"sellerId": str(admin.id), "stock": 100}],
            "mrp": 500.0,
            "isActive": True,
            "isApproved": True,
            "stock": 100,
            "unit": "pcs",
            "isGstCharged": False
        }
        res = await client.post("/api/products/", json=prod3_payload, headers=admin_auth)
        prod3_id = res.json().get("id") or res.json().get("_id")

        # Create a Coupon (10% off)
        coupon_code = f"TEST10-{uuid.uuid4().hex[:4]}"
        coupon_payload = {
            "typeOfDiscount": "total_order_discount",
            "code": coupon_code,
            "method": "discount_code",
            "discountType": "percentage",
            "discountValue": 10.0,
            "validUntil": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
            "appliesToType": "all"
        }
        res = await client.post("/api/coupons/?force=true", json=coupon_payload, headers=admin_auth)
        assert res.status_code in [200, 201], f"Failed to create coupon: {res.text}"

        # Add to Cart
        for pid in [prod1_id, prod2_id, prod3_id]:
            res = await client.post("/api/cart/", json={"productId": str(pid), "quantity": 1}, headers=cust_auth)
            assert res.status_code in [200, 201], f"Cart add failed: {res.text}"

        # Apply Coupon in Checkout
        order_payload = {
            "shippingAddress": {
                "street": "123 Main St", "city": "Test City", "state": "Test State", "zipCode": "123456", "country": "India", "phone": "9999999999"
            },
            "paymentMethod": "cod",
            "couponCode": coupon_code,
            "items": [
                {"productId": str(prod1_id), "quantity": 1, "sellAsCase": False},
                {"productId": str(prod2_id), "quantity": 1, "sellAsCase": False},
                {"productId": str(prod3_id), "quantity": 1, "sellAsCase": False}
            ]
        }
        res = await client.post("/api/orders/", json=order_payload, headers=cust_auth)
        assert res.status_code in [200, 201], f"Order failed: {res.text}"
        order_data = res.json()
        parent_order_id = order_data.get('id') or order_data.get('_id')
        
        print("\n=== MULTI-SELLER COUPON PAYOUT TEST ===")
        print(f"Parent Order Total: {order_data.get('totalAmount')}")
        
        # Mark order as delivered and set suborders as realized
        await order_repository.update(parent_order_id, OrderInternalUpdate(status="delivered"))
        
        sub_orders = await sub_order_repository.findByParentOrder(parent_order_id)
        assert len(sub_orders) == 3
        
        engine = get_async_engine()
        async with engine.begin() as conn:
            for so in sub_orders:
                print(f"  -> SubOrder {so.sub_order_number} | Seller: {so.seller_name} | Subtotal: {so.subtotal} | Discount: {so.discount} | Total: {so.total}")
                await conn.execute(text("UPDATE sj_sub_orders SET status='delivered', commission_status='realized', commission_amount=total*0.10, commission_pct=10 WHERE id=:so_id"), {"so_id": so.id})

        # Trigger Payout for Seller 1
        res = await client.post(f"/api/seller-payouts/settle-all/{str(seller1.id)}", headers=admin_auth)
        assert res.status_code == 201, f"Payout failed: {res.text}"
        p1 = res.json()
        print(f"Seller 1 Payout: {p1['amount']}")

        # Trigger Payout for Seller 2
        res = await client.post(f"/api/seller-payouts/settle-all/{str(seller2.id)}", headers=admin_auth)
        assert res.status_code == 201, f"Payout failed: {res.text}"
        p2 = res.json()
        print(f"Seller 2 Payout: {p2['amount']}")

        # Trigger Payout for Admin
        res = await client.post(f"/api/seller-payouts/settle-all/{str(admin.id)}", headers=admin_auth)
        assert res.status_code == 201, f"Payout failed: {res.text}"
        pa = res.json()
        print(f"Admin Payout: {pa['amount']}")