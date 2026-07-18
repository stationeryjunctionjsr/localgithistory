import uuid
import pytest
from httpx import AsyncClient
from datetime import datetime

from app.repositories.tracking_repository import tracking_repository
from app.repositories.analytics_repository import analytics_repository
from app.repositories.user_repository import user_repository
from app.repositories.session_repository import session_repository

@pytest.fixture
async def admin_auth(client: AsyncClient):
    """Create a temporary admin user, log in, yield auth headers, and clean up."""
    email = f"testadmin_{uuid.uuid4().hex[:8]}@test.com"
    user_data = {
        "name": "Test Admin",
        "email": email,
        "password": "adminpassword123",
        "role": "super_admin",
    }
    user = await user_repository.create(user_data)
    response = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "adminpassword123"},
    )
    token = response.json().get("token", "")
    yield {"Authorization": f"Bearer {token}"}
    try:
        await session_repository.delete_all_for_user(user["_id"])
        await user_repository.storage.delete(user["_id"])
    except Exception:
        pass


@pytest.mark.asyncio
async def test_web_tracking_endpoints(client: AsyncClient):
    """Verify that web event tracking endpoints properly log events in the tracking database."""
    session_id = f"session_web_{uuid.uuid4().hex[:8]}"
    product_id = "prod_web_test_123"
    product_name = "Web Test Product"

    # 1. Search
    res = await client.post("/api/tracking/search", json={
        "searchTerm": "fountain pen",
        "resultsCount": 10,
        "sessionId": session_id,
    })
    assert res.status_code == 200

    # 2. View
    res = await client.post("/api/tracking/view", json={
        "productId": product_id,
        "productName": product_name,
        "sessionId": session_id,
    })
    assert res.status_code == 200

    # 3. Click
    res = await client.post("/api/tracking/click", json={
        "productId": product_id,
        "productName": product_name,
        "source": "homepage_banner",
        "sessionId": session_id,
    })
    assert res.status_code == 200

    # 4. Cart Abandonment
    res = await client.post("/api/tracking/cart-abandonment", json={
        "cartItems": [{"productId": product_id, "quantity": 2, "price": 499.0}],
        "cartValue": 998.0,
        "sessionId": session_id,
    })
    assert res.status_code == 200

    # 5. Session
    res = await client.post("/api/tracking/session", json={
        "sessionId": session_id,
        "isReturning": True,
    })
    assert res.status_code == 200

    # 6. Page View
    res = await client.post("/api/tracking/page-view", json={
        "page": "/products/details",
        "sessionId": session_id,
    })
    assert res.status_code == 200

    # 7. Drop off
    res = await client.post("/api/tracking/drop-off", json={
        "page": "/checkout/step2",
        "reason": "payment_failed",
        "sessionId": session_id,
    })
    assert res.status_code == 200

    # 8. Cart Add
    res = await client.post("/api/tracking/cart-add", json={
        "productId": product_id,
        "quantity": 1,
        "sessionId": session_id,
    })
    assert res.status_code == 200

    # 9. Cart Remove
    res = await client.post("/api/tracking/cart-remove", json={
        "productId": product_id,
        "quantity": 1,
        "sessionId": session_id,
    })
    assert res.status_code == 200

    # 10. Filter Click
    res = await client.post("/api/tracking/filter-click", json={
        "filterType": "category",
        "filterValue": "Pens",
        "sessionId": session_id,
    })
    assert res.status_code == 200

    # Retrieve all logged events for this session from tracking storage
    records = await tracking_repository.storage.findAll({"sessionId": session_id})
    assert len(records) >= 10

    # Validate specific fields of some stored events
    search_record = next(r for r in records if r["type"] == "product_search")
    assert search_record["searchTerm"] == "fountain pen"
    assert search_record["resultsCount"] == 10

    view_record = next(r for r in records if r["type"] == "product_view")
    assert view_record["productId"] == product_id
    assert view_record["productName"] == product_name

    click_record = next(r for r in records if r["type"] == "product_click")
    assert click_record["source"] == "homepage_banner"

    abandon_record = next(r for r in records if r["type"] == "cart_abandonment")
    assert abandon_record["cartValue"] == 998.0

    session_record = next(r for r in records if r["type"] == "session")
    assert session_record["isReturning"] is True

    # Cleanup test tracking events
    await tracking_repository.storage.deleteMany({"sessionId": session_id})


@pytest.mark.asyncio
async def test_mobile_analytics_logging_and_sync(client: AsyncClient):
    """Verify that mobile events logged to /api/analytics/events are logged to the events database and replicated to tracking."""
    session_id = f"session_mobile_{uuid.uuid4().hex[:8]}"
    product_id = "prod_mobile_test_456"
    product_name = "Mobile Test Product"

    mobile_events = [
        {"type": "session_start", "sessionId": session_id, "payload": {"returning": True, "testRunId": session_id}},
        {"type": "page_view", "sessionId": session_id, "page": "/mobile/home", "payload": {"testRunId": session_id}},
        {"type": "product_view", "sessionId": session_id, "payload": {"productId": product_id, "productName": product_name, "testRunId": session_id}},
        {"type": "product_click", "sessionId": session_id, "payload": {"productId": product_id, "productName": product_name, "source": "search_results", "testRunId": session_id}},
        {"type": "add_to_cart", "sessionId": session_id, "payload": {"productId": product_id, "quantity": 3, "testRunId": session_id}},
        {"type": "remove_from_cart", "sessionId": session_id, "payload": {"productId": product_id, "quantity": 1, "testRunId": session_id}},
        {"type": "search", "sessionId": session_id, "payload": {"query": "notebook", "resultsCount": 5, "testRunId": session_id}},
        {"type": "add_to_wishlist", "sessionId": session_id, "payload": {"productId": product_id, "testRunId": session_id}},
        {"type": "begin_checkout", "sessionId": session_id, "payload": {"testRunId": session_id}},
        {"type": "purchase", "sessionId": session_id, "payload": {"testRunId": session_id}},
        {"type": "session_end", "sessionId": session_id, "payload": {"reason": "app_closed", "testRunId": session_id}},
    ]

    for ev in mobile_events:
        res = await client.post("/api/analytics/events", json=ev)
        assert res.status_code == 200
        assert res.json().get("status") == "ok"

    # Verify logging in the events database
    all_event_records = await analytics_repository.event_storage.findAll()
    event_records = [r for r in all_event_records if r.get("payload", {}).get("testRunId") == session_id]
    assert len(event_records) == len(mobile_events)
    
    # Verify replication/syncing in the tracking database
    tracking_records = await tracking_repository.storage.findAll({"sessionId": session_id})
    # begin_checkout translates to page_view (/checkout/step1)
    # purchase translates to page_view (/checkout/complete)
    # so we should have tracking records populated
    assert len(tracking_records) > 0

    track_types = [r["type"] for r in tracking_records]

    # Verify expected event mappings
    assert "session" in track_types  # session_start -> session
    assert "page_view" in track_types  # page_view -> page_view
    assert "product_view" in track_types  # product_view -> product_view
    assert "product_click" in track_types  # product_click -> product_click
    assert "cart_add" in track_types  # add_to_cart -> cart_add
    assert "cart_item_remove" in track_types  # remove_from_cart -> cart_item_remove
    assert "product_search" in track_types  # search -> product_search
    assert "wishlist_add" in track_types  # add_to_wishlist -> wishlist_add
    assert "session_end" in track_types  # session_end -> session_end

    # Verify specific details of replicated records
    rep_search = next(r for r in tracking_records if r["type"] == "product_search")
    assert rep_search["searchTerm"] == "notebook"
    assert rep_search["resultsCount"] == 5

    rep_view = next(r for r in tracking_records if r["type"] == "product_view")
    assert rep_view["productId"] == product_id
    assert rep_view["productName"] == product_name

    rep_checkout = next(r for r in tracking_records if r["type"] == "page_view" and r["page"] == "/checkout/step1")
    assert rep_checkout is not None

    rep_purchase = next(r for r in tracking_records if r["type"] == "page_view" and r["page"] == "/checkout/complete")
    assert rep_purchase is not None

    # Cleanup (since we can't query clob directly, find our specific record IDs to delete)
    for r in event_records:
        await analytics_repository.event_storage.delete(r["_id"])
    await tracking_repository.storage.deleteMany({"sessionId": session_id})


@pytest.mark.asyncio
async def test_analytics_reports_incorporate_events(client: AsyncClient, admin_auth):
    """Verify that the charts and reports endpoints load properly and reflect events."""
    session_id = f"session_test_rep_{uuid.uuid4().hex[:8]}"

    # Inject some events (both direct tracking and replicated mobile events)
    await client.post("/api/tracking/session", json={
        "sessionId": session_id,
        "isReturning": False,
    })
    await client.post("/api/tracking/page-view", json={
        "page": "/products/details",
        "sessionId": session_id,
    })
    # Mobile page view should also sync
    await client.post("/api/analytics/events", json={
        "type": "page_view",
        "sessionId": session_id,
        "page": "/mobile/home",
        "payload": {"testRunId": session_id}
    })

    # Call analytics dashboard/KPI endpoints
    res = await client.get("/api/analytics/kpi", headers=admin_auth)
    assert res.status_code == 200, f"Failed /api/analytics/kpi: {res.status_code} - {res.text}"
    kpi_data = res.json()
    assert "gross_sales" in kpi_data
    assert "returning_customer_rate" in kpi_data

    res = await client.get("/api/analytics/dashboard-data", headers=admin_auth)
    assert res.status_code == 200, f"Failed /api/analytics/dashboard-data: {res.status_code} - {res.text}"

    res = await client.get("/api/analytics/conversion-rate", headers=admin_auth)
    assert res.status_code == 200, f"Failed /api/analytics/conversion-rate: {res.status_code} - {res.text}"
    conv_data = res.json()
    assert "sessions" in conv_data
    assert "added_to_cart" in conv_data
    assert "overall_conversion_rate" in conv_data

    res = await client.get("/api/analytics/checkout-funnel", headers=admin_auth)
    assert res.status_code == 200, f"Failed /api/analytics/checkout-funnel: {res.status_code} - {res.text}"
    funnel_data = res.json()
    assert "cart" in funnel_data
    assert "shipping" in funnel_data
    assert "completed" in funnel_data

    # Cleanup
    await tracking_repository.storage.deleteMany({"sessionId": session_id})
    all_events = await analytics_repository.event_storage.findAll()
    for ev in all_events:
        if ev.get("payload", {}).get("testRunId") == session_id:
            await analytics_repository.event_storage.delete(ev["_id"])
