import asyncio
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.repositories.user_repository import user_repository
from app.repositories.product_repository import product_repository
from app.repositories.category_repository import category_repository
from app.db.storage_factory import get_storage

@pytest.mark.asyncio
async def test_full_e2e_flow():
    # Setup test users
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@test.com"
    seller_email = f"seller_{uuid.uuid4().hex[:6]}@test.com"
    valet_email = f"valet_{uuid.uuid4().hex[:6]}@test.com"
    valet2_email = f"valet2_{uuid.uuid4().hex[:6]}@test.com"
    customer_email = f"cust_{uuid.uuid4().hex[:6]}@test.com"
    test_pincode = f"11{uuid.uuid4().hex[:4]}"

    await user_repository.create({"name": "Admin", "email": admin_email, "password": "pass", "role": "super_admin"})
    await user_repository.create({"name": "Seller", "email": seller_email, "password": "pass", "role": "seller"})
    await user_repository.create({"name": "Valet", "email": valet_email, "password": "pass", "role": "valet", "isOnDuty": True})
    await user_repository.create({"name": "Valet2", "email": valet2_email, "password": "pass", "role": "valet", "isOnDuty": True})
    await user_repository.create({"name": "Customer", "email": customer_email, "password": "pass", "role": "customer", "addresses": [{"pincode": test_pincode, "isDefault": True}]})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login
        async def login(email):
            r = await client.post("/api/auth/login", json={"email": email, "password": "pass"})
            return {"Authorization": f"Bearer {r.json()['token']}"}

        admin_auth = await login(admin_email)
        seller_auth = await login(seller_email)
        valet_auth = await login(valet_email)
        valet2_auth = await login(valet2_email)
        cust_auth = await login(customer_email)

        # 1. Pincode, delivery zone
        zone_payload = {
            "name": f"Test Zone {uuid.uuid4().hex[:4]}",
            "pincodes": [test_pincode],
            "defaultCapacity": 50,
            "urgentDeliveryAvailable": True,
            "isActive": True,
            "customerType": "retail"
        }
        res = await client.post("/api/delivery-zones", json=zone_payload, headers=admin_auth)
        assert res.status_code in (200, 201), f"Zone creation failed: {res.text}"
        zone_id = res.json()["_id"]

        # Slots setup
        slot_payload = {
            "zoneId": zone_id,
            "isActive": True,
            "slots": [
                {
                    "startTime": "00:00",
                    "endTime": "23:59",
                    "isActive": True,
                    "isUrgent": False,
                    "capacity": 100,
                    "cutoffHours": 0
                },
                {
                    "startTime": "00:00",
                    "endTime": "23:59",
                    "isActive": True,
                    "isUrgent": True,
                    "capacity": 50,
                    "cutoffHours": 0
                }
            ]
        }
        res = await client.post(f"/api/delivery-slots/{zone_id}", json=slot_payload, headers=admin_auth)
        assert res.status_code in (200, 201), f"Slot creation failed: {res.text}"

        print("1. Delivery Zone & Slots created successfully.")

        # 2. Seller assigning themselves to the zones
        res = await client.put("/api/users/seller-delivery-settings", json={"serviceableZoneIds": [zone_id]}, headers=seller_auth)
        assert res.status_code == 200, f"Seller zone assignment failed: {res.text}"
        print("2. Seller assigned to zone successfully.")

        # Admin assigns Valet to zone
        valet_res = await client.get("/api/auth/me", headers=valet_auth)
        valet_id = valet_res.json()["_id"]
        valet2_res = await client.get("/api/auth/me", headers=valet2_auth)
        valet2_id = valet2_res.json()["_id"]
        
        res = await client.put(f"/api/users/{valet_id}", json={"serviceAreaZones": [zone_id], "role": "valet"}, headers=admin_auth)
        assert res.status_code == 200, f"Admin assign valet to zone failed: {res.text}"
        res = await client.put(f"/api/users/{valet2_id}", json={"serviceAreaZones": [zone_id], "role": "valet"}, headers=admin_auth)
        assert res.status_code == 200

        # 3. Valet assigning themselves to the zones for the day
        from datetime import datetime, timezone
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        valet_avail = {
            "date": today_str,
            "availabilityType": "full_day",
            "zones": [zone_id]
        }
        res = await client.put("/api/valet-availability/my-availability", json=valet_avail, headers=valet_auth)
        assert res.status_code == 200, f"Valet availability failed: {res.text}"
        res = await client.put("/api/valet-availability/my-availability", json=valet_avail, headers=valet2_auth)
        assert res.status_code == 200

        print("3. Valets assigned themselves to the zones successfully.")

        # 4. Seller adding products
        # Create Category
        cat_res = await client.post("/api/categories", json={"name": f"Cat {uuid.uuid4().hex[:4]}", "isActive": True}, headers=admin_auth)
        assert cat_res.status_code in (200, 201), f"Category creation failed: {cat_res.text}"
        cat_id = cat_res.json()["_id"]

        # Create Product as Admin
        prod_payload = {
            "name": f"Prod {uuid.uuid4().hex[:4]}",
            "category": cat_id,
            "mrp": 100.0,
            "price": 90.0,
            "stock": 100,
            "isActive": True
        }
        prod_res = await client.post("/api/products", json=prod_payload, headers=admin_auth)
        assert prod_res.status_code in (200, 201), f"Product creation failed: {prod_res.text}"
        prod_id = prod_res.json()["_id"]

        seller_user_res = await client.get("/api/auth/me", headers=seller_auth)
        seller_id = seller_user_res.json()["_id"]
        
        await product_repository.storage.update(prod_id, {"catalogSellerIds": [seller_id]})
        print("4. Product created and seller added to product.")

        # 5. Customer adds to cart and checkout
        res = await client.post("/api/cart/add", json={"productId": prod_id, "quantity": 1}, headers=cust_auth)
        assert res.status_code == 200, f"Cart add failed: {res.text}"

        res = await client.get("/api/delivery-slots/available", params={"pincode": test_pincode, "segment": "retail", "date": today_str})
        assert res.status_code == 200, f"Get slots failed: {res.text}"
        slots_data = res.json()
        assert len(slots_data) > 0, f"No delivery slots available for customer, zone_id={zone_id}, pincode={test_pincode}"
        selected_slot = slots_data[0]

        checkout_payload = {
            "address": {"pincode": test_pincode, "city": "Delhi", "state": "Delhi", "addressLine1": "Test Addr", "name": "Cust", "phone": "9999999999"},
            "deliverySlotId": selected_slot["configId"],
            "deliverySlotDate": today_str,
            "isUrgent": False,
            "paymentMethod": "cod"
        }
        res = await client.post("/api/orders/checkout", json=checkout_payload, headers=cust_auth)
        assert res.status_code in (200, 201), f"Checkout failed: {res.text}"
        order_data = res.json()
        order_id = order_data["_id"]
        print("5. Checkout successful.", order_id)

        # 6. Valet assignment, cascading
        from app.jobs.valet_timeout_job import tick_valet_assignments
        # Call tick to trigger assignments
        await tick_valet_assignments(app)
        print("6. Valet cascading triggered")
        
        # Admin gets order to see assigned valet
        res = await client.get(f"/api/orders/{order_id}", headers=admin_auth)
        order_info = res.json()
        assert "assignedValet" in order_info, "Valet was not assigned"
        print("Order assigned to valet:", order_info["assignedValet"])
        
        return True
