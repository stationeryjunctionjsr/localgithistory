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
    from app.models.referral_settings import ReferralSettings
    legacy_settings = ReferralSettings(
        id="1",
        retail={"segment": "retail", "discountType": "percentage", "discountValue": 12.5, "isActive": True},
    )
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
    from app.models.referral_settings import ReferralSettings
    settings_payload = ReferralSettings(
        retail={"segment": "retail", "discountType": "percentage", "discountValue": 10.0, "isActive": True},
        business={"segment": "business", "discountType": "percentage", "discountValue": 0.0, "isActive": False},
    )
    await referral_repository.update_settings(settings_payload)

    # Mock delivery charge for East Singhbhum (831001) to make pincode serviceable
    from app.models.daos_flat import DeliveryChargeInternalCreate
    pincode_data = DeliveryChargeInternalCreate(
        pincode="831001",
        state="Jharkhand",
        district="East Singhbhum",
        city="Jamshedpur",
        charge=50.0,
        minCartValue=500.0,
        serviceableForCustomer=True,
        isActive=True,
    )
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
    ref_code = referrer.referral_code
    assert ref_code is not None

    # 4. Verify code (valid case)
    verify_resp = await client.post("/api/referrals/verify", json={"code": ref_code}, headers=user_auth)
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["valid"] is True
    assert verify_data["discountType"] == "percentage"
    assert verify_data["discountValue"] == 10.0
    assert verify_data["referrerName"] in ["Referrer User", "Test User"]

    # 5. Verify invalid code (should fail)
    invalid_verify = await client.post("/api/referrals/verify", json={"code": "INVALID123"}, headers=user_auth)
    assert invalid_verify.status_code == 400

    # 6. Verify own code (should fail)
    # Get current user's profile to find their own referral code
    from app.utils.auth import verify_token

    token = user_auth["Authorization"].split(" ")[1]
    curr_user_claims = await verify_token(token)
    curr_user = await user_repository.findById(curr_user_claims.id)
    own_code = curr_user.referral_code

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
    from app.models.daos import ProductInternalCreate
    product_data = ProductInternalCreate(
        name="Test Referral Product",
        sku="SKU-REF-TEST",
        mrp=200.0,
        price=200.0,
        stock=10,
        isActive=True,
        gst=18.0,
        category="Test Category",
    )
    existing_product = await product_repository.findBySku("SKU-REF-TEST")
    if existing_product:
        try:
            from app.config.database import get_async_session_factory
            from sqlalchemy import text
            factory = get_async_session_factory()
            async with factory() as session:
                await session.execute(text("DELETE FROM sj_order_items WHERE product_id = :pid"), {"pid": int(existing_product.id)})
                await session.commit()
            await product_repository.storage.delete(existing_product.id)
            product = await product_repository.create(product_data)
        except Exception:
            product = existing_product
    else:
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
        "items": [{"productId": str(product.id), "quantity": 1}],
        "referralCode": ref_code,
    }
    from unittest.mock import patch, AsyncMock
    with patch("app.repositories.feature_flag_repository.FeatureFlagRepository.is_enabled", new_callable=AsyncMock, return_value=True):
        order_resp = await client.post("/api/orders/", json=order_payload, headers=user_auth)
    assert order_resp.status_code == 201
    order_data = order_resp.json()

    # Discount should be 10% of subtotal-before-referral (product price 200.0 -> discount 20.0)
    assert round(order_data["discount"], 2) == 20.0
    notes_val = order_data["orderNotes"] if "orderNotes" in order_data and order_data["orderNotes"] else (order_data["notes"] if "notes" in order_data and order_data["notes"] else "")
    assert "Referral Code Applied: " + ref_code in notes_val

    # 9. Verify that user is no longer eligible (since they placed 1 order)
    eligibility_resp2 = await client.get("/api/referrals/check-eligibility", headers=user_auth)
    assert eligibility_resp2.status_code == 200
    assert eligibility_resp2.json()["eligible"] is False

    # 10. Verify code verification now fails
    verify_resp2 = await client.post("/api/referrals/verify", json={"code": ref_code}, headers=user_auth)
    assert verify_resp2.status_code == 400

    # Clean up
    try:
        from app.config.database import get_async_session_factory
        from sqlalchemy import text
        factory = get_async_session_factory()
        async with factory() as session:
            await session.execute(text("DELETE FROM sj_order_items WHERE product_id = :pid"), {"pid": int(product.id)})
            await session.commit()
    except Exception:
        pass
    try:
        await order_repository.storage.delete(order_data["_id"])
    except Exception:
        pass
    try:
        await product_repository.storage.delete(product.id)
    except Exception:
        pass
    try:
        await user_repository.storage.delete(referrer.id)
    except Exception:
        pass
    if not existing_pincode:
        try:
            await delivery_charge_repository.storage.delete("831001")
        except Exception:
            pass

    # Restore active retail settings to 12.5%
    await referral_repository.storage.delete("1")
    from app.models.referral_settings import ReferralSettings
    await referral_repository.update_settings(
        ReferralSettings(
            retail={"segment": "retail", "discountType": "percentage", "discountValue": 12.5, "isActive": True},
            business={"segment": "business", "discountType": "percentage", "discountValue": 0.0, "isActive": False},
        )
    )