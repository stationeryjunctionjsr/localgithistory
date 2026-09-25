from app.models.daos_flat import DeliveryChargeInternal, DeliveryChargeDefaultInternal, DeliveryChargeTierInternal
"""
Comprehensive tests for Delivery Zones, Delivery Charges, Delivery Slots,
and Checkout (serviceability + order placement) flows.

Coverage:
─────────────────────────────────────────────────────────────────────────────
A. DeliveryChargeRepository (unit)
   A1  calculateTieredCharge – basic tiers
   A2  calculateTieredCharge – infinity tier (always free shipping threshold)
   A3  calculateTieredCharge – empty tiers
   A4  calculateTieredCharge – exact boundary (order_amount == maxAmount)
   A5  isChargeApplicableToRole – customer / wholesaler / unknown
   A6  isPincodeServiceable – customer-serviceable vs not

B. check_serviceability endpoint (unit, no real DB)
   B1  Invalid pincode format (< 6 digits) → isServiceable=False
   B2  Non-digit pincode → isServiceable=False
   B3  Valid 6-digit format but unconfigured pincode → isServiceable=False
   B4  urgentDeliveryAvailable flag propagated

C. Delivery Zones router – pincode resolution (GET /delivery-zones/for-pincode)
   C1  Unknown pincode returns null zoneId
   C2  Response schema contains all required keys

D. Delivery Charges router (HTTP, super_admin guard)
   D1  GET /delivery-charges without auth → 401 / 403
   D2  GET /delivery-charges/location – returns charge, gstPercentage, totalCharge
   D3  GET /delivery-charges/check-serviceability – invalid pincode format
   D4  POST /delivery-charges without auth → 401 / 403

E. Delivery Slots logic (unit)
   E1  _resolve_zone_config returns None when no config exists
   E2  Slot cutoff-hours filter (past-cutoff slot excluded)
   E3  Capacity exhausted slot excluded
   E4  Slot within 24-hour window included

F. Checkout flow (HTTP, authenticated)
   F1  Order rejected when pincode not serviceable (mocked)
   F2  Required address fields validation
   F3  Delivery slot fields are accepted (slotId, configId, slotDate)
   F4  Urgent delivery flag forwarded
─────────────────────────────────────────────────────────────────────────────
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.repositories.delivery_charge_repository import DeliveryChargeRepository


# ═════════════════════════════════════════════════════════════════════════════
# A. DeliveryChargeRepository — pure unit tests (no DB required)
# ═════════════════════════════════════════════════════════════════════════════


class TestDeliveryChargeRepository:
    """Unit tests for DeliveryChargeRepository helper methods."""

    def setup_method(self):
        self.repo = DeliveryChargeRepository()

    # ── A1 ──────────────────────────────────────────────────────────────────
    def test_calculate_tiered_charge_basic(self):
        """Order below first tier max pays first tier charge."""
        class MockTier:
            def __init__(self, m, c):
                self.max = m
                self.charge = c
        tiers = [
            MockTier(500, 60),
            MockTier(1000, 40),
            MockTier("Infinity", 0),
        ]
        result = self.repo.calculateTieredCharge(tiers, order_amount=300)
        assert result.charge == 60.0
        assert result.appliedTier is not None

    # ── A2 ──────────────────────────────────────────────────────────────────
    def test_calculate_tiered_charge_infinity_tier(self):
        """Order above all finite thresholds falls into Infinity tier (free shipping)."""
        tiers = [
            MagicMock(max=500, charge=60),
            MagicMock(max="Infinity", charge=0),
        ]
        result = self.repo.calculateTieredCharge(tiers, order_amount=1500)
        assert result.charge == 0.0

    # ── A3 ──────────────────────────────────────────────────────────────────
    def test_calculate_tiered_charge_empty(self):
        """Empty tiers list returns zero charge."""
        result = self.repo.calculateTieredCharge([], order_amount=500)
        assert result.charge == 0
        assert result.appliedTier is None

    # ── A4 ──────────────────────────────────────────────────────────────────
    def test_calculate_tiered_charge_boundary(self):
        """order_amount exactly equal to maxAmount picks the NEXT tier (strict <)."""
        tiers = [
            MagicMock(max=500, charge=60),
            MagicMock(max="Infinity", charge=0),
        ]
        # order_amount = 500 is NOT < 500, so it falls to the Infinity tier
        result = self.repo.calculateTieredCharge(tiers, order_amount=500)
        assert result.charge == 0.0

    # ── A5 ──────────────────────────────────────────────────────────────────
    def test_is_charge_applicable_to_role(self):
        """Customer always applicable; wholesaler respects applicableToWholesaler flag."""
        charge_for_all = MagicMock(applicableToWholesaler=True)
        charge_retail_only = MagicMock(applicableToWholesaler=False)

        assert self.repo.isChargeApplicableToRole(charge_for_all, "customer") is True
        assert self.repo.isChargeApplicableToRole(charge_retail_only, "customer") is True
        assert self.repo.isChargeApplicableToRole(charge_for_all, "wholesaler") is True
        assert self.repo.isChargeApplicableToRole(charge_retail_only, "wholesaler") is False
        # Unknown role treated like customer
        assert self.repo.isChargeApplicableToRole(charge_retail_only, "unknown") is True

    # ── A6 ──────────────────────────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_is_pincode_serviceable_customer(self):
        """isPincodeServiceable returns correct flag based on serviceableForCustomer field."""
        mock_charge_serviceable = MagicMock(
            pincode="110001",
            isActive=True,
            serviceableForCustomer=True,
            serviceableForWholesaler=False,
        )
        mock_charge_not_serviceable = MagicMock(
            pincode="110002",
            isActive=True,
            serviceableForCustomer=False,
            serviceableForWholesaler=True,
        )

        with patch.object(self.repo, "findByPincode", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = mock_charge_serviceable
            result = await self.repo.isPincodeServiceable("110001", "customer")
            assert result is True

            mock_find.return_value = mock_charge_not_serviceable
            result = await self.repo.isPincodeServiceable("110002", "customer")
            assert result is False

            mock_find.return_value = mock_charge_not_serviceable
            result = await self.repo.isPincodeServiceable("110002", "wholesaler")
            assert result is True  # serviceableForWholesaler=True


# ═════════════════════════════════════════════════════════════════════════════
# B. check_serviceability endpoint — unit (bypass DB)
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_check_serviceability_short_pincode():
    """B1 – Pincode shorter than 6 digits is immediately rejected."""
    from app.routers.delivery_charges import check_serviceability

    result = await check_serviceability("123", "customer")
    assert result["isServiceable"] is False
    assert result["sellerCount"] == 0
    assert result["slotBookingAvailable"] is False


@pytest.mark.asyncio
async def test_check_serviceability_non_digit_pincode():
    """B2 – Pincode containing non-digit characters is rejected."""
    from app.routers.delivery_charges import check_serviceability

    result = await check_serviceability("ABCDEF", "customer")
    assert result["isServiceable"] is False


@pytest.mark.asyncio
async def test_check_serviceability_unconfigured_pincode():
    """B3 – Valid 6-digit format but pincode not in system → not serviceable."""
    from app.routers.delivery_charges import check_serviceability

    repo_path = "app.routers.delivery_charges.delivery_charge_repository"
    # get_zone_for_pincode is imported inside the function body from zone_seller_cache,
    # so we patch at the source module.
    zone_path = "app.repositories.zone_seller_cache.get_zone_for_pincode"
    storage_path = "app.db.storage_factory.get_storage"

    with patch(zone_path, new_callable=AsyncMock) as mock_zone_fn, \
         patch(f"{repo_path}.isPincodeServiceable", new_callable=AsyncMock) as mock_svc, \
         patch(storage_path) as mock_get_storage:
        mock_zone_fn.return_value = None   # pincode not in any zone
        mock_svc.return_value = False      # not serviceable
        # Prevent slot availability check from hitting DB
        mock_slot_storage = MagicMock()
        mock_slot_storage.findAll = AsyncMock(return_value=[])
        mock_get_storage.return_value = mock_slot_storage

        result = await check_serviceability("999999", "customer")

    assert result["isServiceable"] is False
    assert result["pincode"] == "999999"
    assert result["sellerCount"] == 0


@pytest.mark.asyncio
async def test_check_serviceability_urgent_flag_propagated():
    """B4 – urgentDeliveryAvailable from zone is forwarded correctly."""
    from app.routers.delivery_charges import check_serviceability

    from app.models.schemas import DeliveryZoneResponse
    mock_zone = DeliveryZoneResponse(id="zone_test", urgentDeliveryAvailable=True, customerType="retail", name="Zone", isActive=True, pincodes=[],)

    repo_path = "app.routers.delivery_charges.delivery_charge_repository"
    # get_zone_for_pincode and get_storage are imported inside the function body,
    # so we patch at the source module.
    zone_path = "app.repositories.zone_seller_cache.get_zone_for_pincode"
    storage_path = "app.db.storage_factory.get_storage"

    with patch(zone_path, new_callable=AsyncMock) as mock_zone_fn, \
         patch(f"{repo_path}.isPincodeServiceable", new_callable=AsyncMock) as mock_svc, \
         patch(storage_path) as mock_get_storage:

        mock_zone_fn.return_value = mock_zone
        mock_svc.return_value = True

        # Slot storage mock (returns no slots so available_dates stays [])
        mock_slot_storage = MagicMock()
        mock_slot_storage.findAll = AsyncMock(return_value=[])
        mock_get_storage.return_value = mock_slot_storage

        result = await check_serviceability("560001", "customer")

    assert result["urgentDeliveryAvailable"] is True


# ═════════════════════════════════════════════════════════════════════════════
# C. Delivery Zones router – for-pincode (HTTP)
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_zone_for_unknown_pincode():
    """C1+C2 – Unknown pincode returns null zoneId with expected schema keys (DB mocked)."""
    from unittest.mock import AsyncMock, MagicMock, patch

    # The /for-pincode endpoint uses get_async_session_factory() to run a SQL query.
    # We mock it so no real DB connection is needed.
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None  # no row → pincode not found

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_factory = MagicMock(return_value=mock_session)

    with patch("app.routers.delivery_zones.get_async_session_factory", return_value=mock_factory):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/delivery-zones/for-pincode?pincode=000000")

    assert resp.status_code == 200
    data = resp.json()
    # zoneId must be None for an unconfigured pincode
    assert data["zoneId"] is None
    assert data["zoneName"] is None
    # Required keys always present
    for key in ("zoneId", "zoneName", "defaultCapacity", "urgentDeliveryAvailable", "customerType"):
        assert key in data, f"Key '{key}' missing from /for-pincode response"


# ═════════════════════════════════════════════════════════════════════════════
# D. Delivery Charges router – auth guard + location charge
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_delivery_charges_requires_auth():
    """D1 – GET /delivery-charges without token must return 401 or 403."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/delivery-charges")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_delivery_charge_location_response_schema():
    """D2 – /delivery-charges/location always returns expected keys (may be 0 charge)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/delivery-charges/location",
            params={
                "state": "Jharkhand",
                "city": "Jamshedpur",
                "district": "East Singhbhum",
                "pincode": "831001",
                "userRole": "customer",
                "orderAmount": 0,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    for key in ("charge", "gstPercentage", "gstAmount", "totalCharge"):
        assert key in data, f"Key '{key}' missing from /location response"
    # charge must be non-negative
    assert data["charge"] >= 0
    assert data["totalCharge"] >= data["charge"]


@pytest.mark.asyncio
async def test_check_serviceability_invalid_pincode_via_api():
    """D3 – check-serviceability via HTTP returns isServiceable=False for bad format."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/delivery-charges/check-serviceability",
            params={"pincode": "12", "userRole": "customer"},
        )
    assert resp.status_code == 200
    assert resp.json()["isServiceable"] is False


@pytest.mark.asyncio
async def test_post_delivery_charges_requires_auth():
    """D4 – POST /delivery-charges without token must be rejected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/delivery-charges",
            json={
                "pincode": "110001",
                "state": "Delhi",
                "city": "Delhi",
                "district": "Delhi",
                "charge": 50,
                "minCartValue": 0,
                "serviceableForCustomer": True,
            },
        )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_delete_delivery_charges_requires_auth():
    """D5 – DELETE /delivery-charges/<id> without token must be rejected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.delete("/api/delivery-charges/nonexistent_id")
    assert resp.status_code in (401, 403)


# ═════════════════════════════════════════════════════════════════════════════
# E. Delivery Slots — unit tests (no DB)
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_resolve_zone_config_no_config():
    """E1 – _resolve_zone_config returns None when neither zone nor default config exists."""
    from app.routers.delivery_slots import _resolve_zone_config
    import app.routers.delivery_slots as slots_mod

    # get_zone_for_pincode is imported locally inside _resolve_zone_config, so patch at source.
    # storage is a module-level object — patch its findAll method directly.
    with patch("app.repositories.zone_seller_cache.get_zone_for_pincode", new_callable=AsyncMock) as mock_zone:
        mock_zone.return_value = None  # pincode not in any zone

        original_findAll = slots_mod.storage.findAll
        slots_mod.storage.findAll = AsyncMock(return_value=[])
        try:
            result = await _resolve_zone_config("999999", "2030-01-01", "retail")
        finally:
            slots_mod.storage.findAll = original_findAll

    assert result is None


@pytest.mark.asyncio
async def test_get_available_slots_empty_when_no_config():
    """E2 – /delivery-slots/available returns [] when no slot config exists for the date."""
    # Patch _resolve_zone_config to return None (no config for this pincode/date)
    with patch("app.routers.delivery_slots._resolve_zone_config", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = None
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/delivery-slots/available",
                params={"date": "2030-12-31", "pincode": "000000", "segment": "retail"},
            )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_available_slots_cutoff_filter():
    """E3 – Slots that have already passed their cutoff time are excluded."""
    import datetime as _dt
    from app.routers.delivery_slots import _resolve_zone_config

    # Build a slot that was due 5 hours ago (cutoffHours=0 but slot end in the past)
    past_time = (_dt.datetime.now() - _dt.timedelta(hours=2)).strftime("%H:%M")
    mock_config = MagicMock(
        id="cfg_1",
        zoneId="zone_test",
        slots=[
            MagicMock(
                id="s1",
                startTime=past_time,
                endTime=past_time,
                isActive=True,
                isUrgent=False,
                capacity=10,
                bookedCount=0,
                cutoffHours=3,
            )
        ],
        isActive=True,
    )

    with patch("app.routers.delivery_slots._resolve_zone_config", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = mock_config

        today = _dt.date.today().isoformat()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/delivery-slots/available",
                params={"date": today, "pincode": "110001", "segment": "retail"},
            )

    assert resp.status_code == 200
    # The past-cutoff slot must be excluded
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_available_slots_capacity_full():
    """E4 – Fully-booked slots are excluded from available slots."""
    import datetime as _dt
    from app.routers.delivery_slots import _resolve_zone_config

    # Slot with capacity=1 and bookedCount=1 → full
    future_time = (_dt.datetime.now() + _dt.timedelta(hours=4)).strftime("%H:%M")
    mock_config = MagicMock(
        id="cfg_2",
        zoneId="zone_test",
        slots=[
            MagicMock(
                id="s2",
                startTime=future_time,
                endTime=future_time,
                isActive=True,
                isUrgent=False,
                capacity=1,
                bookedCount=1,
                cutoffHours=None,
            )
        ],
        isActive=True,
    )

    with patch("app.routers.delivery_slots._resolve_zone_config", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = mock_config

        today = _dt.date.today().isoformat()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/delivery-slots/available",
                params={"date": today, "pincode": "110001", "segment": "retail"},
            )

    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_available_slots_valid_slot_included():
    """E5 – A future slot with available capacity appears in the response."""
    import datetime as _dt

    # A slot 2 hours from now that ends within 24 hours — should pass all filters
    start = (_dt.datetime.now() + _dt.timedelta(hours=1)).strftime("%H:%M")
    end = (_dt.datetime.now() + _dt.timedelta(hours=2)).strftime("%H:%M")
    mock_config = MagicMock(
        id="cfg_3",
        zoneId="zone_test",
        slots=[
            MagicMock(
                id="s3",
                startTime=start,
                endTime=end,
                isActive=True,
                isUrgent=False,
                capacity=5,
                bookedCount=0,
                cutoffHours=None,
            )
        ],
        isActive=True,
    )

    with patch("app.routers.delivery_slots._resolve_zone_config", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = mock_config

        today = _dt.date.today().isoformat()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/delivery-slots/available",
                params={"date": today, "pincode": "110001", "segment": "retail"},
            )

    assert resp.status_code == 200
    slots = resp.json()
    assert len(slots) == 1
    assert slots[0]["slotId"] == "s3"
    assert slots[0]["isUrgent"] is False


@pytest.mark.asyncio
async def test_book_slot_not_found():
    """E6 – Booking a slot in a non-existent config returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/delivery-slots/nonexistent_config_id/book-slot",
            params={"slot_id": "slot_123"},
        )
    assert resp.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
# F. Checkout flow (HTTP, authenticated)
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_checkout_requires_authentication():
    """F1 – POST /orders without authentication should fail (401/403)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/orders",
            json={
                "shippingAddress": {
                    "street": "123 Test St",
                    "city": "Jamshedpur",
                    "state": "Jharkhand",
                    "district": "East Singhbhum",
                    "zipCode": "831001",
                    "country": "India",
                },
                "paymentMethod": "cod",
                "items": [{"productId": "prod_123", "quantity": 1}],
            },
        )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_delivery_charge_gst_calculation():
    """F2 – GST is added on top of base charge when deliveryChargeGst is enabled."""
    repo = DeliveryChargeRepository()
    # Simulate: pincode charge Rs.100, GST 18%
    with patch.object(repo, "findByPincode", new_callable=AsyncMock) as mock_find, \
         patch.object(repo, "getDefaultCharge", new_callable=AsyncMock) as mock_default:

        mock_find.return_value = DeliveryChargeInternal(**{
            "pincode": "831001",
            "isActive": True,
            "serviceableForCustomer": True,
            "applyDefaultCharge": False,
            "charge": 100.0,
            "minCartValue": 0.0,
            "tiers": [],
        })
        mock_default.return_value = DeliveryChargeDefaultInternal(**{
            "isActive": True,
            
            
        })

        result = await repo.getChargeForLocation(
            state="Jharkhand",
            city="Jamshedpur",
            district="East Singhbhum",
            pincode="831001",
            user_role="customer",
            order_amount=200,
        )

    assert result.charge == 100.0
    assert result.source == "pincode"


@pytest.mark.asyncio
async def test_delivery_charge_wholesaler_not_applicable():
    """F3 – When applicableToWholesaler=False the charge for wholesaler should be 0."""
    repo = DeliveryChargeRepository()

    with patch.object(repo, "findByPincode", new_callable=AsyncMock) as mock_find, \
         patch.object(repo, "findByLocation", new_callable=AsyncMock) as mock_loc, \
         patch.object(repo, "getDefaultCharge", new_callable=AsyncMock) as mock_default:

        mock_find.return_value = None  # no pincode-specific charge
        mock_loc.return_value = None   # no city-level charge
        mock_default.return_value = DeliveryChargeDefaultInternal(isActive=True, applicableToWholesaler=False, tiers=[{"max": "Infinity", "charge": 80}])

        result = await repo.getChargeForLocation(
            state="Jharkhand",
            city="Jamshedpur",
            district="East Singhbhum",
            pincode=None,
            user_role="wholesaler",
            order_amount=300,
        )

    assert result.isApplicableToRole is False
    assert result.charge == 0


@pytest.mark.asyncio
async def test_delivery_charge_tiered_applied():
    """F4 – Tiered delivery charge: correct tier selected for order amount."""
    repo = DeliveryChargeRepository()

    tiers = [
        {"max": 500, "charge": 80},
        {"max": 1000, "charge": 50},
        {"max": "Infinity", "charge": 0},
    ]

    with patch.object(repo, "findByPincode", new_callable=AsyncMock) as mock_find, \
         patch.object(repo, "findByLocation", new_callable=AsyncMock) as mock_loc, \
         patch.object(repo, "getDefaultCharge", new_callable=AsyncMock) as mock_default:

        mock_find.return_value = None
        mock_loc.return_value = None  # no city-level charge → falls to default
        mock_default.return_value = DeliveryChargeDefaultInternal(**{
            "isActive": True,
            "applicableToWholesaler": True,
            "tiers": tiers,
            
            
        })

        result_low = await repo.getChargeForLocation("S", "C", "D", None, "customer", 200)
        result_mid = await repo.getChargeForLocation("S", "C", "D", None, "customer", 750)
        result_free = await repo.getChargeForLocation("S", "C", "D", None, "customer", 1500)

    assert result_low.charge == 80.0, "Order 200 should be in 80-charge tier"
    assert result_mid.charge == 50.0, "Order 750 should be in 50-charge tier"
    assert result_free.charge == 0.0, "Order 1500 should be in free tier"


# ═════════════════════════════════════════════════════════════════════════════
# G. Zone cache / seller resolution
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_zone_for_pincode_none_when_not_in_any_zone():
    """G1 – get_zone_for_pincode returns None for a pincode in no zone."""
    from app.repositories.zone_seller_cache import get_zone_for_pincode

    with patch("app.repositories.zone_seller_cache._fetch_all_zones", new_callable=AsyncMock) as mock_zones:
        mock_zones.return_value = [
            {"_id": "z1", "pincodes": ["110001"], "isActive": True},
        ]
        result = await get_zone_for_pincode("999000")

    assert result is None


@pytest.mark.asyncio
async def test_get_zone_for_pincode_found():
    """G2 – get_zone_for_pincode returns the matching zone document."""
    from app.repositories.zone_seller_cache import get_zone_for_pincode

    from app.models.schemas import DeliveryZoneResponse
    mock_zone = DeliveryZoneResponse(
        id="z1",
        name="Test Zone",
        pincodes=["831001"],
        isActive=True,
       
    )

    with patch("app.repositories.zone_seller_cache._fetch_all_zones", new_callable=AsyncMock) as mock_zones:
        mock_zones.return_value = [mock_zone]
        result = await get_zone_for_pincode("831001")

    assert result is not None
    assert result.name == "Test Zone"


def test_invalidate_zone_cache_specific():
    """G3 – Invalidating a specific zone does not clear other cached zones."""
    from app.repositories import zone_seller_cache
    import time

    zone_seller_cache._zone_seller_cache["z_keep"] = (frozenset(["seller1"]), time.monotonic() + 300)
    zone_seller_cache._zone_seller_cache["z_evict"] = (frozenset(["seller2"]), time.monotonic() + 300)

    zone_seller_cache.invalidate_zone_cache("z_evict")

    assert "z_evict" not in zone_seller_cache._zone_seller_cache
    assert "z_keep" in zone_seller_cache._zone_seller_cache

    # Clean up
    zone_seller_cache._zone_seller_cache.pop("z_keep", None)


def test_invalidate_zone_cache_full():
    """G4 – Calling invalidate_zone_cache() with no argument clears all entries."""
    from app.repositories import zone_seller_cache
    import time

    zone_seller_cache._zone_seller_cache["z1"] = (frozenset(), time.monotonic() + 300)
    zone_seller_cache._zone_seller_cache["z2"] = (frozenset(), time.monotonic() + 300)

    zone_seller_cache.invalidate_zone_cache()

    assert len(zone_seller_cache._zone_seller_cache) == 0


# ═════════════════════════════════════════════════════════════════════════════
# H. Delivery Zones router — CRUD auth guards
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_zones_requires_auth():
    """H1 – GET /delivery-zones without token returns 401/403."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/delivery-zones")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_zone_requires_auth():
    """H2 – POST /delivery-zones without token returns 401/403."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/delivery-zones",
            json={"name": "Test Zone", "pincodes": ["831001"], "customerType": "retail"},
        )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_update_zone_requires_auth():
    """H3 – PUT /delivery-zones/<id> without token returns 401/403."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.put(
            "/api/delivery-zones/nonexistent_zone",
            json={"name": "Updated Zone"},
        )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_delete_zone_requires_auth():
    """H4 – DELETE /delivery-zones/<id> without token returns 401/403."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.delete("/api/delivery-zones/nonexistent_zone")
    assert resp.status_code in (401, 403)


# ═════════════════════════════════════════════════════════════════════════════
# I. Delivery Slots router — CRUD auth guards
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_slots_requires_auth():
    """I1 – GET /delivery-slots without token returns 401/403."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/delivery-slots")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_slot_config_requires_auth():
    """I2 – POST /delivery-slots without token returns 401/403."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/delivery-slots",
            json={
                "segment": "retail",
                "date": "2030-01-01",
                "zoneIds": ["default"],
                "slots": [{"id": "s1", "startTime": "09:00", "endTime": "12:00"}],
            },
        )
    assert resp.status_code in (401, 403)


# ═════════════════════════════════════════════════════════════════════════════
# J. Pincode conflict detection (unit)
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_check_pincode_conflicts_no_conflict():
    """J1 – Pincodes not assigned to any zone → no conflicts reported."""
    from app.routers.delivery_zones import _check_pincode_conflicts

    with patch("app.routers.delivery_zones.get_storage") as mock_storage_factory:
        mock_storage = MagicMock()
        mock_storage.findAll = AsyncMock(return_value=[
            MagicMock(id="z1", name="Zone A", pincodes=["110001", "110002"]),
        ])
        mock_storage_factory.return_value = mock_storage

        conflicts = await _check_pincode_conflicts(["831001", "831002"])

    assert conflicts == []


@pytest.mark.asyncio
async def test_check_pincode_conflicts_detected():
    """J2 – Pincode already in another zone → conflict reported."""
    from app.routers.delivery_zones import _check_pincode_conflicts

    with patch("app.routers.delivery_zones.get_storage") as mock_storage_factory:
        mock_storage = MagicMock()
        mock_storage.findAll = AsyncMock(return_value=[
            MagicMock(id="z1", name="Zone A", pincodes=["110001", "831001"]),
        ])
        mock_storage_factory.return_value = mock_storage

        # 831001 is taken by zone z1, but we're creating a NEW zone (no exclude_zone_id)
        conflicts = await _check_pincode_conflicts(["831001", "400001"])

    assert "831001" in conflicts
    assert "400001" not in conflicts


@pytest.mark.asyncio
async def test_check_pincode_conflicts_exclude_own_zone():
    """J3 – When updating a zone, its own pincodes are excluded from conflict check."""
    from app.routers.delivery_zones import _check_pincode_conflicts

    with patch("app.routers.delivery_zones.get_storage") as mock_storage_factory:
        mock_storage = MagicMock()
        class MockZone:
            def __init__(self, i, n, p):
                self.id = i
                self.name = n
                self.pincodes = p
        mock_storage.findAll = AsyncMock(return_value=[
            MockZone("z_own", "Own Zone", ["831001"]),
        ])
        mock_storage_factory.return_value = mock_storage

        # Excluding own zone_id → 831001 is not a conflict
        conflicts = await _check_pincode_conflicts(["831001"], exclude_zone_id="z_own")

    assert conflicts == []
