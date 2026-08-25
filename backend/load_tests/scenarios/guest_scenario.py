"""
Guest Scenario
==============
Simulates an unauthenticated visitor browsing the store.
Weight: ~60 % of total traffic (highest).

Typical flow:
  1. Hit the health endpoint (sanity)
  2. Load homepage data (banners, categories, promos)
  3. Browse product listing with filters
  4. View a single product
  5. Check recommendations / trending
  6. Lookup a pincode
"""

import random
from locust import TaskSet, between, task


PRODUCT_IDS_SAMPLE = [
    # Will be populated dynamically from /api/products on first run
]

CATEGORY_IDS_SAMPLE = [
    # Will be populated dynamically from /api/categories on first run
]

SEARCH_TERMS = [
    "notebook",
    "pen",
    "pencil",
    "stapler",
    "file",
    "folder",
    "eraser",
    "sharpener",
    "marker",
    "highlighter",
    "ruler",
    "calculator",
    "sticky",
    "tape",
    "scissors",
]

PINCODES = ["831001", "831002", "831003", "110001", "400001", "560001"]


class GuestBrowsing(TaskSet):
    """
    Task set for unauthenticated guest users.
    Higher task weights = more frequent execution.
    """

    def on_start(self):
        """Pre-populate product/category IDs once per user."""
        self._product_ids = list(PRODUCT_IDS_SAMPLE)
        self._category_ids = list(CATEGORY_IDS_SAMPLE)
        self._warm_up()

    def _warm_up(self):
        """Fetch a product listing page to cache product IDs."""
        try:
            resp = self.client.get(
                "/api/products/public?page=1&limit=20",
                name="/api/products/public [warm-up]",
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

    # ── Tasks ─────────────────────────────────────────────────────────────────

    @task(1)
    def health_check(self):
        self.client.get("/api/health", name="/api/health")

    @task(10)
    def browse_products(self):
        page = random.randint(1, 3)
        self.client.get(
            f"/api/products/public?page={page}&limit=20",
            name="/api/products/public",
        )

    @task(5)
    def browse_products_by_search(self):
        term = random.choice(SEARCH_TERMS)
        self.client.get(
            f"/api/products/public?search={term}&page=1&limit=20",
            name="/api/products/public?search=",
        )

    @task(3)
    def browse_categories(self):
        self.client.get("/api/categories/public", name="/api/categories/public")

    @task(4)
    def view_banners(self):
        self.client.get("/api/banners/public", name="/api/banners/public")

    @task(2)
    def view_brands(self):
        self.client.get("/api/brands/public", name="/api/brands/public")

    @task(2)
    def view_collections(self):
        self.client.get("/api/collections/public", name="/api/collections/public")

    @task(3)
    def view_promo_strips(self):
        self.client.get("/api/promo-strips", name="/api/promo-strips")

    @task(2)
    def view_recommendations(self):
        self.client.get(
            "/api/recommendations",
            name="/api/recommendations",
        )

    @task(6)
    def view_product_detail(self):
        if not self._product_ids:
            self.browse_products()
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
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(1)
    def check_pincode(self):
        pincode = random.choice(PINCODES)
        self.client.get(
            f"/api/delivery-charges/check-serviceability?pincode={pincode}",
            name="/api/delivery-charges/check-serviceability",
        )

    @task(1)
    def check_search_tags(self):
        self.client.get("/api/search-tags", name="/api/search-tags")

    @task(1)
    def check_app_version(self):
        self.client.get("/api/app/version", name="/api/app/version")
