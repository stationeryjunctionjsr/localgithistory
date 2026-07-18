"""
Customer Scenario
=================
Simulates an authenticated customer making purchases.
Weight: ~30 % of total traffic.

Requires TEST_CUSTOMER_TOKEN env var (a valid JWT for a customer account).
If no token is provided, authenticated endpoints are skipped and the user
falls back to guest-like browsing.

Typical flow:
  1. Browse products
  2. Add items to cart
  3. View cart
  4. Apply coupon
  5. Browse wishlist
  6. View order history
  7. Check notifications
"""

import os
import random
from locust import TaskSet, between, task

# Pull token from env — set this before running authenticated tests
CUSTOMER_TOKEN = os.getenv("TEST_CUSTOMER_TOKEN", "")

SEARCH_TERMS = [
    "notebook", "pen", "pencil", "stapler", "file",
    "eraser", "marker", "highlighter", "ruler",
]

COUPON_CODES = ["WELCOME10", "SAVE20", "FIRST", "TEST123"]


class CustomerShopping(TaskSet):
    """
    Task set for authenticated customer users.
    Includes cart, wishlist, orders, and notification flows.
    """

    def on_start(self):
        self._token = CUSTOMER_TOKEN
        self._product_ids = []
        self._has_auth = bool(self._token)
        self._auth_headers = (
            {"Authorization": f"Bearer {self._token}"} if self._has_auth else {}
        )
        self._warm_up()

    def _warm_up(self):
        """Fetch products to get real IDs for cart/wishlist operations."""
        try:
            resp = self.client.get(
                "/api/products/public?page=1&limit=20",
                name="/api/products/public [customer warm-up]",
                catch_response=True,
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("products", data.get("items", []))
                for item in items[:10]:
                    pid = item.get("id") or item.get("productId")
                    if pid:
                        self._product_ids.append(pid)
                resp.success()
            else:
                resp.failure(f"warm-up failed: {resp.status_code}")
        except Exception:
            pass

    # ── Public Tasks (no auth needed) ─────────────────────────────────────────

    @task(8)
    def browse_products(self):
        page = random.randint(1, 3)
        self.client.get(
            f"/api/products/public?page={page}&limit=20",
            name="/api/products/public",
        )

    @task(5)
    def search_products(self):
        term = random.choice(SEARCH_TERMS)
        self.client.get(
            f"/api/products/public?search={term}&page=1&limit=20",
            name="/api/products/public?search=",
        )

    @task(4)
    def view_product_detail(self):
        if not self._product_ids:
            return
        pid = random.choice(self._product_ids)
        with self.client.get(
            f"/api/products/public/{pid}",
            name="/api/products/public/[id]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected {resp.status_code}")

    @task(2)
    def browse_categories(self):
        self.client.get("/api/categories/public", name="/api/categories/public")

    # ── Authenticated Tasks ────────────────────────────────────────────────────

    @task(6)
    def view_cart(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/cart",
            headers=self._auth_headers,
            name="/api/cart [GET]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Cart GET failed: {resp.status_code}")

    @task(3)
    def add_to_cart(self):
        if not self._has_auth or not self._product_ids:
            return
        pid = random.choice(self._product_ids)
        payload = {"productId": pid, "quantity": 1}
        with self.client.post(
            "/api/cart",
            json=payload,
            headers=self._auth_headers,
            name="/api/cart [POST]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 400, 404, 422):
                # 400/422 = product not found or stock issue — still a valid response
                resp.success()
            else:
                resp.failure(f"Add to cart failed: {resp.status_code}")

    @task(2)
    def view_wishlist(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/wishlist",
            headers=self._auth_headers,
            name="/api/wishlist [GET]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Wishlist GET failed: {resp.status_code}")

    @task(4)
    def view_orders(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/orders?page=1&limit=10",
            headers=self._auth_headers,
            name="/api/orders [customer]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Orders GET failed: {resp.status_code}")

    @task(2)
    def view_notifications(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/notifications",
            headers=self._auth_headers,
            name="/api/notifications [GET]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Notifications failed: {resp.status_code}")

    @task(1)
    def check_referrals(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/referrals",
            headers=self._auth_headers,
            name="/api/referrals [GET]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Referrals failed: {resp.status_code}")

    @task(1)
    def validate_coupon(self):
        """Simulate checking whether a coupon code is valid."""
        if not self._has_auth:
            return
        code = random.choice(COUPON_CODES)
        with self.client.get(
            f"/api/coupons/validate?code={code}",
            headers=self._auth_headers,
            name="/api/coupons/validate",
            catch_response=True,
        ) as resp:
            # 400 / 404 = invalid coupon — still a valid backend response
            if resp.status_code in (200, 400, 404, 422):
                resp.success()
            else:
                resp.failure(f"Coupon validate failed: {resp.status_code}")
