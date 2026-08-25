"""
Admin Scenario
==============
Simulates admin panel operations.
Weight: ~10 % of total traffic.

Requires TEST_ADMIN_TOKEN env var (a valid JWT for an admin account).
All tasks are skipped gracefully when no token is provided.

Typical admin flow:
  - Poll analytics dashboard
  - List and paginate orders
  - View user list
  - Manage products (read-heavy; no destructive writes during load tests)
  - View support tickets
  - Check notifications
"""

import os
import random
from locust import TaskSet, between, task

ADMIN_TOKEN = os.getenv("TEST_ADMIN_TOKEN", "")

ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]


class AdminOperations(TaskSet):
    """
    Task set for admin panel users.
    Read-heavy — avoids writing/deleting real data during load tests.
    """

    def on_start(self):
        self._token = ADMIN_TOKEN
        self._has_auth = bool(self._token)
        self._auth_headers = {"Authorization": f"Bearer {self._token}"} if self._has_auth else {}

    # ── Dashboard & Analytics ─────────────────────────────────────────────────

    @task(10)
    def analytics_dashboard(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/analytics/dashboard",
            headers=self._auth_headers,
            name="/api/analytics/dashboard",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Analytics dashboard: {resp.status_code}")

    @task(3)
    def analytics_revenue(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/analytics/revenue",
            headers=self._auth_headers,
            name="/api/analytics/revenue",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403, 404):
                resp.success()
            else:
                resp.failure(f"Analytics revenue: {resp.status_code}")

    # ── Order Management ──────────────────────────────────────────────────────

    @task(8)
    def list_orders(self):
        if not self._has_auth:
            return
        page = random.randint(1, 5)
        status = random.choice([None] + ORDER_STATUSES)
        url = f"/api/orders?page={page}&limit=20"
        if status:
            url += f"&status={status}"
        with self.client.get(
            url,
            headers=self._auth_headers,
            name="/api/orders [admin list]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Orders list: {resp.status_code}")

    # ── User Management ───────────────────────────────────────────────────────

    @task(4)
    def list_users(self):
        if not self._has_auth:
            return
        page = random.randint(1, 3)
        with self.client.get(
            f"/api/users?page={page}&limit=20",
            headers=self._auth_headers,
            name="/api/users [admin list]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Users list: {resp.status_code}")

    # ── Product Management ────────────────────────────────────────────────────

    @task(5)
    def list_products_admin(self):
        if not self._has_auth:
            return
        page = random.randint(1, 5)
        with self.client.get(
            f"/api/products?page={page}&limit=20&role=admin",
            headers=self._auth_headers,
            name="/api/products [admin]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Products admin: {resp.status_code}")

    # ── Support & Notifications ───────────────────────────────────────────────

    @task(2)
    def list_support_tickets(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/support-tickets?page=1&limit=20",
            headers=self._auth_headers,
            name="/api/support-tickets [admin]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Support tickets: {resp.status_code}")

    @task(2)
    def list_returns(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/returns?page=1&limit=20",
            headers=self._auth_headers,
            name="/api/returns [admin]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Returns: {resp.status_code}")

    @task(1)
    def list_notifications(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/notifications",
            headers=self._auth_headers,
            name="/api/notifications [admin]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Notifications: {resp.status_code}")

    @task(1)
    def list_customer_segments(self):
        if not self._has_auth:
            return
        with self.client.get(
            "/api/customer-segments",
            headers=self._auth_headers,
            name="/api/customer-segments [admin]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Customer segments: {resp.status_code}")
