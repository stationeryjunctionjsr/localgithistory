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
from app.models.daos import CategoryInternalCreate, ProductInternalCreate

@pytest.mark.asyncio
async def test_full_returns_e2e_flow():
    # Setup test users
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@test.com"
    seller_email = f"seller_{uuid.uuid4().hex[:8]}@test.com"
    valet_email = f"valet_{uuid.uuid4().hex[:8]}@test.com"
    customer_email = f"cust_{uuid.uuid4().hex[:8]}@test.com"

    await user_repository.create(UserCreate(name="Admin", email=admin_email, password="pass", role="super_admin"))
    await user_repository.create(UserCreate(name="Seller", email=seller_email, password="pass", role="seller"))
    
    valet = await user_repository.create(UserCreate(name="Valet", email=valet_email, password="pass", role="valet", isOnDuty=True, isApproved=True, serviceablePincodes=["123456"]))
    
    # Create Zone for customer's pincode
    from app.db.storage_factory import get_storage
    zone_storage = get_storage("deliveryZones")
    all_zones = await zone_storage.findAll()
    zone_doc = None
    for z in all_zones:
        if "123456" in str(z.pincodes or ""):
            zone_doc = z
            break
    if not zone_doc:
        from app.models.daos_flat import DeliveryZoneInternalCreate
        zone_doc = await zone_storage.create(DeliveryZoneInternalCreate(name="Test Zone", pincodes=["123456"], isActive=True))
    zone_id = str(zone_doc.id)
    
    # Create Valet Availability
    avail_storage = get_storage("valetAvailability")
    from datetime import date as dt_date
    from app.models.daos import ValetAvailabilityInternalCreate
    avail = await avail_storage.create(ValetAvailabilityInternalCreate(**{
        "valetId": str(valet.id),
        "date": dt_date.today().isoformat(),
        "availabilityType": "full_day",
        "zones": [zone_id],
        "slots": []
    }))
    print("Created AVAIL:", avail)
    found_avail = await avail_storage.findAll({"date": dt_date.today().isoformat()})
    print("Found AVAIL:", found_avail)


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
        cat_doc = await cat_storage.create(CategoryInternalCreate(name=f"Returns Category {uuid.uuid4().hex[:8]}", isActive=True, gst=18.0))
        
        prod_doc = await product_repository.create(ProductInternalCreate(
            name="Returnable Product",
            mrp=100.0, price=90.0,
            category=cat_doc.name,
            stock=10,
            isActive=True,
            isReturnable=True
            
        ))
        prod_id = str(prod_doc.id)

        # Place an Order
        cart_payload = {"productId": prod_id, "quantity": 1}
        await client.post("/api/cart", json=cart_payload, headers=cust_auth)
        
        checkout_payload = {
            "shippingAddress": {"street": "123 Test St", "city": "Test", "state": "TS", "pincode": "123456"},
            "paymentMethod": "cod"
        }
        res = await client.post("/api/orders", json=checkout_payload, headers=cust_auth)
        assert res.status_code in (200, 201)
        order_id = res.json()["_id"]

        # Mark order as delivered so it can be returned
        now_iso = datetime.now(timezone.utc).isoformat()
        from app.models.order import OrderInternalUpdate
        await order_repository.update(order_id, OrderInternalUpdate(status="delivered", deliveredAt=now_iso))

        # Check Eligibility
        res = await client.get(f"/api/returns/order/{order_id}/eligibility", headers=cust_auth)
        assert res.status_code == 200, res.text
        eligibility = res.json()
        
        # Debug DB
        db_order = await order_repository.findById(order_id)
        print("DB ORDER:", db_order)
        db_prod = await product_repository.findById(prod_id)
        print("DB PRODUCT:", db_prod)
        from app.repositories.category_repository import category_repository
        db_cat = await category_repository.findByName(db_prod.category)
        print("DB CAT:", db_cat)
        
        print("ELIGIBILITY RESULT:", eligibility)
        assert len(eligibility["eligibleItems"]) > 0, f"No items eligible for return! Reason: {eligibility.get('reason')}"


        # Request Return
        return_payload = {
            "orderId": order_id,
            "items": [{"productId": prod_id, "quantity": 1, "price": 100.0, "reason": "Defective"}],
            "paymentMethod": "wallet"
        }
        res = await client.post("/api/returns/request", json=return_payload, headers=cust_auth)
        assert res.status_code == 200, f"Return request failed: {res.text}"
        return_id = res.json()["_id"]

        # Admin Auto-assigns valet
        res = await client.post(f"/api/returns/admin/{return_id}/auto-assign", headers=admin_auth)
        assert res.status_code == 200, f"Auto-assign failed: {res.text}"
        
        print("Returns E2E Flow successful!")