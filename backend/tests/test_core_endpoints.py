"""Core smoke tests with meaningful assertions.

Fixtures (client, user_auth) come from conftest.py.
"""

import pytest


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Login with wrong password must return 401, not silently succeed."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpassword"},
    )
    assert response.status_code in (400, 401, 404), (
        f"Expected 400/401/404 for bad credentials, got {response.status_code}"
    )


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client):
    """Accessing /api/users/profile without a token must be rejected."""
    response = await client.get("/api/users/profile")
    assert response.status_code in (401, 403), f"Unauthenticated request should be rejected, got {response.status_code}"


@pytest.mark.asyncio
async def test_user_profile(client, user_auth):
    """Authenticated user can read their own profile."""
    response = await client.get("/api/users/profile", headers=user_auth)
    assert response.status_code == 200, f"Expected 200 for authenticated profile, got {response.status_code}"
    data = response.json()
    assert "email" in data or "_id" in data or "id" in data, "Profile response should contain user data"


@pytest.mark.asyncio
async def test_orders_list(client, user_auth):
    """Authenticated user can fetch their order list (even if empty)."""
    response = await client.get("/api/orders/", headers=user_auth)
    assert response.status_code == 200, f"Expected 200 for orders list, got {response.status_code}"


@pytest.mark.asyncio
async def test_wishlist_list(client, user_auth):
    """Authenticated user can fetch their wishlist (even if empty)."""
    response = await client.get("/api/wishlist/", headers=user_auth)
    assert response.status_code == 200, f"Expected 200 for wishlist, got {response.status_code}"


@pytest.mark.asyncio
async def test_categories_public(client):
    """Categories endpoint is public and returns a list."""
    response = await client.get("/api/categories/public")
    assert response.status_code == 200, f"Expected 200 for public categories, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Categories should return a JSON array"


@pytest.mark.asyncio
async def test_brands_public(client):
    """Brands endpoint is public and returns a list."""
    response = await client.get("/api/brands/public")
    assert response.status_code == 200, f"Expected 200 for public brands, got {response.status_code}"
    assert isinstance(response.json(), list), "Brands should return a JSON array"


@pytest.mark.asyncio
async def test_payment_status_unknown_order(client, user_auth):
    """Requesting payment status for a nonexistent order returns 404, not 500."""
    response = await client.get("/api/payments/status/nonexistent-order-id", headers=user_auth)
    assert response.status_code in (404, 400), f"Nonexistent payment should return 404/400, got {response.status_code}"


@pytest.mark.asyncio
async def test_returns_list(client, user_auth):
    """Authenticated user can fetch their returns (even if empty)."""
    response = await client.get("/api/returns/my-returns", headers=user_auth)
    assert response.status_code == 200, f"Expected 200 for returns list, got {response.status_code}"


@pytest.mark.asyncio
async def test_analytics_requires_admin(client, user_auth):
    """Analytics endpoint requires admin role — regular users must be rejected."""
    response = await client.get("/api/analytics/kpi", headers=user_auth)
    assert response.status_code in (401, 403), f"Regular user should not access analytics, got {response.status_code}"


@pytest.mark.asyncio
async def test_support_tickets_list_requires_auth(client):
    """Accessing /api/support-tickets/ without a token must be rejected."""
    response = await client.get("/api/support-tickets/")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_support_tickets_workflow(client, user_auth):
    """Create a ticket, check that it's in the list, and view it by ID."""
    ticket_payload = {
        "name": "Test User",
        "email": "testuser@test.com",
        "phone": "9876543210",
        "company": "Test Company",
        "subject": "Test Ticket Subject",
        "description": "This is a test ticket description.",
        "category": "general",
        "priority": "medium",
    }
    response = await client.post("/api/support-tickets/", json=ticket_payload, headers=user_auth)
    assert response.status_code == 201
    ticket = response.json()
    assert ticket["subject"] == "Test Ticket Subject"
    assert ticket["description"] == "This is a test ticket description."
    assert ticket["status"] == "open"
    ticket_id = ticket["_id"]

    response = await client.get("/api/support-tickets/", headers=user_auth)
    assert response.status_code == 200
    tickets = response.json()
    assert any(t["_id"] == ticket_id for t in tickets)

    response = await client.get(f"/api/support-tickets/{ticket_id}", headers=user_auth)
    assert response.status_code == 200
    ticket_fetched = response.json()
    assert ticket_fetched["_id"] == ticket_id
    assert ticket_fetched["subject"] == "Test Ticket Subject"