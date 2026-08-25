"""Cart endpoint tests.

Fixtures (client, user_auth) come from conftest.py.
"""

import pytest


@pytest.mark.asyncio
async def test_get_cart_authenticated(client, user_auth):
    """Authenticated user can fetch their cart (returns 200 with a list/dict, not 500)."""
    response = await client.get("/api/cart/", headers=user_auth)
    assert response.status_code == 200, f"Expected 200 for empty cart, got {response.status_code}"


@pytest.mark.asyncio
async def test_get_cart_unauthenticated(client):
    """Accessing cart without authentication must be rejected."""
    response = await client.get("/api/cart/")
    assert response.status_code in (401, 403), (
        f"Unauthenticated cart access should be rejected, got {response.status_code}"
    )


@pytest.mark.asyncio
async def test_add_invalid_product_to_cart(client, user_auth):
    """Adding a nonexistent product to cart returns 404, not 500."""
    response = await client.post(
        "/api/cart/",
        headers=user_auth,
        json={"productId": "nonexistent-product-id", "quantity": 1},
    )
    assert response.status_code in (400, 404, 422), (
        f"Adding invalid product should return 400/404/422, got {response.status_code}"
    )
