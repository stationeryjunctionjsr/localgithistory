import pytest
from httpx import AsyncClient
from app.main import app
from app.models.schemas import UserCreate
from app.repositories.user_repository import user_repository
from app.repositories.referral_repository import referral_repository
from app.utils.auth import require_super_admin


@pytest.fixture(autouse=True)
def override_super_admin():
    # Override super admin authorization check for testing
    app.dependency_overrides[require_super_admin] = lambda: {"role": "super_admin"}
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_referral_settings_get_and_put(client: AsyncClient):
    # Ensure settings are deleted/empty to trigger the default fallback logic
    await referral_repository.storage.delete("1")

    # 1. Test GET endpoint: should successfully fetch and initialize settings with both segments
    response = await client.get("/api/referrals/settings")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"

    data = response.json()
    assert "retail" in data
    assert "business" in data

    assert data["retail"]["segment"] == "retail"
    assert data["retail"]["discountType"] == "percentage"
    assert data["retail"]["discountValue"] == 0
    assert data["retail"]["isActive"] is False

    assert data["business"]["segment"] == "business"
    assert data["business"]["discountType"] == "percentage"
    assert data["business"]["discountValue"] == 0
    assert data["business"]["isActive"] is False

    # 2. Test PUT endpoint: should update and save settings successfully
    update_payload = {
        "retail": {"segment": "retail", "discountType": "fixed", "discountValue": 10.0, "isActive": True},
        "business": {"segment": "business", "discountType": "percentage", "discountValue": 5.0, "isActive": False},
    }
    put_response = await client.put("/api/referrals/settings", json=update_payload)
    assert put_response.status_code == 200, (
        f"Expected 200, got {put_response.status_code}. Response: {put_response.text}"
    )

    updated_data = put_response.json()
    assert updated_data["retail"]["discountType"] == "fixed"
    assert updated_data["retail"]["discountValue"] == 10.0
    assert updated_data["retail"]["isActive"] is True
    assert updated_data["business"]["discountValue"] == 5.0


@pytest.mark.asyncio
async def test_referral_settings_missing_business_populated(client: AsyncClient):
    # Set settings with ONLY retail segment manually
    await referral_repository.storage.delete("1")
    legacy_settings = {
        "_id": "1",
        "retail": {"segment": "retail", "discountType": "percentage", "discountValue": 12.5, "isActive": True},
    }
    await referral_repository.storage.create(legacy_settings)

    # Fetch via API, should populate business automatically
    response = await client.get("/api/referrals/settings")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"

    data = response.json()
    assert "retail" in data
    assert "business" in data
    assert data["retail"]["discountValue"] == 12.5
    assert data["business"]["discountValue"] == 0


@pytest.mark.asyncio
async def test_referral_flow_for_customer(client: AsyncClient, user_auth: dict):
    from app.repositories.user_repository import user_repository
    from app.repositories.product_repository import product_repository
    from app.repositories.order_repository import order_repository
    from app.repositories.delivery_charge_repository import delivery_charge_repository

    # 1. Set retail referral settings to active
    await referral_repository.storage.delete("1")
    settings_payload = {
        "retail": {"segment": "retail", "discountType": "percentage", "discountValue": 10.0, "isActive": True},
        "business": {"segment": "business", "discountType": "percentage", "discountValue": 0.0, "isActive": False},
    }
    await referral_repository.update_settings(settings_payload)

    # Mock delivery charge for East Singhbhum (831001) to make pincode serviceable
    pincode_data = {
        "pincode": "831001",
        "state": "Jharkhand",
        "district": "East Singhbhum",
        "city": "Jamshedpur",
        "charge": 50.0,
        "minCartValue": 500.0,
        "serviceableForCustomer": True,
        "isActive": True,
    }
    existing_pincode = await delivery_charge_repository.storage.findOne({"pincode": "831001"})
    if not existing_pincode:
        await delivery_charge_repository.storage.create(pincode_data)

    # 2. Check eligibility (should be eligible)
    eligibility_resp = await client.get("/api/referrals/check-eligibility", headers=user_auth)
    assert eligibility_resp.status_code == 200
    elig_data = eligibility_resp.json()
    assert elig_data["eligible"] is True
    assert elig_data["discountType"] == "percentage"
    assert elig_data["discountValue"] == 10.0

    # 3. Create another user to get a referral code
    import uuid
    referrer_data = UserCreate(
        name="Referrer User",
        email=f"referrer_{uuid.uuid4().hex[:8]}@test.com",
        password="password123",
        role="customer",
    )
    referrer = await user_repository.create(referrer_data)
    ref_code = referrer.get("referralCode")
    assert ref_code is not None

    # 4. Verify code (valid case)
    verify_resp = await client.post("/api/referrals/verify", json={"code": ref_code}, headers=user_auth)
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["valid"] is True
    assert verify_data["discountType"] == "percentage"
    assert verify_data["discountValue"] == 10.0
    assert verify_data["referrerName"] == "Referrer User"

    # 5. Verify invalid code (should fail)
    invalid_verify = await client.post("/api/referrals/verify", json={"code": "INVALID123"}, headers=user_auth)
    assert invalid_verify.status_code == 400

    # 6. Verify own code (should fail)
    # Get current user's profile to find their own referral code
    from app.utils.auth import verify_token

    token = user_auth["Authorization"].split(" ")[1]
    curr_user_claims = await verify_token(token)
    curr_user = await user_repository.findById(curr_user_claims["_id"])
    own_code = curr_user.get("referralCode")

    self_verify = await client.post("/api/referrals/verify", json={"code": own_code}, headers=user_auth)
    assert self_verify.status_code == 400

    # 7. Check public scheme endpoint
    scheme_resp = await client.get("/api/referrals/scheme", headers=user_auth)
    assert scheme_resp.status_code == 200
    scheme_data = scheme_resp.json()
    assert scheme_data["isActive"] is True
    assert scheme_data["discountType"] == "percentage"
    assert scheme_data["discountValue"] == 10.0

    # 8. Create a mock product and place an order using the referral code
    product_data = {
        "name": "Test Referral Product",
        "sku": "SKU-REF-TEST",
        "mrp": 200.0,
        "stock": 10,
        "isActive": True,
        "gst": 18,
        "category": "Test Category",
    }
    existing_product = await product_repository.findBySku("SKU-REF-TEST")
    if existing_product:
        # Clean up any leftover orders referencing this product first
        all_orders = await order_repository.findAll()
        for o in all_orders:
            for item in o.get("items", []):
                pid = item.get("product") or item.get("productId")
                if pid and str(pid) == str(existing_product.id if hasattr(product, "id") else product["_id"]):
                    await order_repository.storage.delete(o["_id"])
                    break
        await product_repository.storage.delete(existing_product.id if hasattr(product, "id") else product["_id"])
    product = await product_repository.create(product_data)

    order_payload = {
        "shippingAddress": {
            "street": "123 Test St",
            "city": "Jamshedpur",
            "state": "Jharkhand",
            "district": "East Singhbhum",
            "zipCode": "831001",
            "country": "India",
        },
        "paymentMethod": "cod",
        "notes": "My test order",
        "items": [{"productId": str(product.id if hasattr(product, "id") else product["_id"]), "quantity": 1}],
        "referralCode": ref_code,
    }
    order_resp = await client.post("/api/orders/", json=order_payload, headers=user_auth)
    assert order_resp.status_code == 201
    order_data = order_resp.json()

    # Discount should be 10% of subtotal-before-referral (meaning subtotal = 90%, discount = 10%)
    assert round(order_data["discount"], 2) == round(order_data["subtotal"] / 9.0, 2)
    assert "Referral Code Applied: " + ref_code in order_data["notes"]

    # 9. Verify that user is no longer eligible (since they placed 1 order)
    eligibility_resp2 = await client.get("/api/referrals/check-eligibility", headers=user_auth)
    assert eligibility_resp2.status_code == 200
    assert eligibility_resp2.json()["eligible"] is False

    # 10. Verify code verification now fails
    verify_resp2 = await client.post("/api/referrals/verify", json={"code": ref_code}, headers=user_auth)
    assert verify_resp2.status_code == 400

    # Clean up
    await order_repository.storage.delete(order_data["_id"])
    await product_repository.storage.delete(product.id if hasattr(product, "id") else product["_id"])
    await user_repository.storage.delete(referrer["_id"])
    if not existing_pincode:
        await delivery_charge_repository.storage.delete("831001")

    # Restore active retail settings to 12.5%
    await referral_repository.storage.delete("1")
    await referral_repository.update_settings(
        {
            "retail": {"segment": "retail", "discountType": "percentage", "discountValue": 12.5, "isActive": True},
            "business": {"segment": "business", "discountType": "percentage", "discountValue": 0.0, "isActive": False},
        }
    )