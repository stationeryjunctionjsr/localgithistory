import pytest
import uuid
import logging
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.repositories.user_repository import user_repository
from app.models.schemas import UserCreate
from app.repositories.sub_order_repository import sub_order_repository
from app.repositories.sub_order_repository import sub_order_repository

@pytest.mark.asyncio
async def test_multiseller_suborder_split():
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@test.com"
    seller1_email = f"seller1_{uuid.uuid4().hex[:8]}@test.com"
    seller2_email = f"seller2_{uuid.uuid4().hex[:8]}@test.com"
    customer_email = f"customer_{uuid.uuid4().hex[:8]}@test.com"

    # Create Users
    admin = await user_repository.create(UserCreate(name="Admin", email=admin_email, password="pass", role="super_admin"))
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
        cat_payload = {"name": f"Test Category {uuid.uuid4().hex[:4]}", "isActive": True, "commissionPercentage": 5.0}
        res = await client.post("/api/categories/", json=cat_payload, headers=admin_auth)
        cat_id = res.json().get("id") or res.json().get("_id")

        # Create Product for Seller 1
        prod1_payload = {
            "name": f"Seller1 Prod {uuid.uuid4().hex[:4]}",
            "categoryId": cat_id,
            "sellers": [{"sellerId": str(seller1.id), "stock": 100}],
            "mrp": 1000.0,
            "price": 800.0,
            "isActive": True,
            "isApproved": True,
            "stock": 100,
            "pincodes": ["123456"],
            "unit": "pcs",
            "isGstCharged": False
        }
        res = await client.post("/api/products/", json=prod1_payload, headers=admin_auth)
        assert res.status_code in [200, 201], res.text
        prod1_id = res.json().get("id") or res.json().get("_id")

        # Create Product for Seller 2
        prod2_payload = {
            "name": f"Seller2 Prod {uuid.uuid4().hex[:4]}",
            "categoryId": cat_id,
            "sellers": [{"sellerId": str(seller2.id), "stock": 100}],
            "mrp": 500.0,
            "price": 400.0,
            "isActive": True,
            "isApproved": True,
            "stock": 100,
            "pincodes": ["123456"],
            "unit": "pcs",
            "isGstCharged": False
        }
        res = await client.post("/api/products/", json=prod2_payload, headers=admin_auth)
        assert res.status_code in [200, 201], res.text
        prod2_id = res.json().get("id") or res.json().get("_id")

                # Add to Cart
        res1 = await client.post("/api/cart/", json={"productId": str(prod1_id), "quantity": 1}, headers=cust_auth)
        assert res1.status_code in [200, 201], f"Cart 1 failed: {res1.text}"
        res2 = await client.post("/api/cart/", json={"productId": str(prod2_id), "quantity": 1}, headers=cust_auth)
        assert res2.status_code in [200, 201], f"Cart 2 failed: {res2.text}"

        # Checkout
        order_payload = {
            "shippingAddress": {
                "street": "123 Main St",
                "city": "Test City",
                "state": "Test State",
                "zipCode": "123456",
                "country": "India",
                "phone": "9999999999"
            },
            "billingAddress": {
                "street": "123 Main St",
                "city": "Test City",
                "state": "Test State",
                "zipCode": "123456",
                "country": "India",
                "phone": "9999999999"
            },
            "items": [
                {"productId": str(prod1_id), "quantity": 1, "sellAsCase": False},
                {"productId": str(prod2_id), "quantity": 1, "sellAsCase": False}
            ]
        }
        res = await client.post("/api/orders/", json=order_payload, headers=cust_auth)
        assert res.status_code in [200, 201], res.text
        order_data = res.json()

        print("\n=== MULTI-SELLER ORDER PLACED ===")
        print(f"Parent Order Total: {order_data.get('totalAmount')}")
        print(f"Parent Delivery Fee: {order_data.get('deliveryFee')}")
        
        parent_order_id = order_data.get('id') or order_data.get('_id')
        sub_orders = await sub_order_repository.findByParentOrder(parent_order_id)
        
        print(f"Sub-Orders Created: {len(sub_orders)}")

        for so in sub_orders:
            print(f"  -> SubOrder {so.sub_order_number} | Seller: {so.seller_name} | Subtotal: {so.subtotal} | Shipping: {so.shipping}")

        assert len(sub_orders) == 2, f"Expected 2 sub-orders, got {len(sub_orders)}"
        
        shipping1 = sub_orders[0].shipping
        shipping2 = sub_orders[1].shipping
        assert shipping1 == 0.0 and shipping2 == 0.0, "Sub-orders should not carry delivery charges!"





