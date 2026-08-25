"""
Load Test Configuration
=======================
Central config for all Locust load tests and the benchmark runner.
Adjust BASE_URL if the API runs on a different host/port.
"""

import os

# ── Target ────────────────────────────────────────────────────────────────────
BASE_URL = os.getenv("LOAD_TEST_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("LOAD_TEST_FRONTEND_URL", "http://localhost:3000")

# ── Locust ramp-up profiles ───────────────────────────────────────────────────
PROFILES = {
    "baseline": {
        "users": 1,
        "spawn_rate": 1,
        "run_time": "30s",
        "description": "Single user — establishes clean baseline latency",
    },
    "load": {
        "users": 50,
        "spawn_rate": 5,
        "run_time": "2m",
        "description": "Normal load — 50 concurrent users ramped at 5/s",
    },
    "stress": {
        "users": 100,
        "spawn_rate": 10,
        "run_time": "3m",
        "description": "Stress — 100 users, exceeds DB pool (35 connections)",
    },
    "spike": {
        "users": 200,
        "spawn_rate": 50,
        "run_time": "1m",
        "description": "Spike — 200 users spawned very fast then drops back",
    },
    "high_load": {
        "users": 500,
        "spawn_rate": 20,
        "run_time": "3m",
        "description": "High load — 500 concurrent users",
    },
}

# ── Report output directory ───────────────────────────────────────────────────
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

# ── SLA thresholds (milliseconds / percentages) ───────────────────────────────
SLA = {
    # Response time percentiles
    "p50_ms": 200,
    "p90_ms": 500,
    "p99_ms": 1500,
    # Error rate
    "error_rate_pct": 1.0,  # max 1 % errors under normal load
    "stress_error_rate_pct": 5.0,  # max 5 % errors under stress
    # Throughput
    "min_rps": 10,  # minimum requests/second under load
}

# ── Endpoints tested by benchmark_endpoints.py ────────────────────────────────
PUBLIC_ENDPOINTS = [
    ("GET", "/api/health", "Health check"),
    ("GET", "/api/products/public?page=1&limit=20", "Products - page 1"),
    ("GET", "/api/products/public?page=2&limit=20", "Products - page 2"),
    ("GET", "/api/categories/public", "Categories"),
    ("GET", "/api/banners/public", "Banners"),
    ("GET", "/api/brands/public", "Brands"),
    ("GET", "/api/collections/public", "Collections"),
    ("GET", "/api/promo-strips", "Promo strips"),
    ("GET", "/api/recommendations", "Trending recommendations"),
    ("GET", "/api/search-tags", "Search tags"),
    ("GET", "/api/delivery-charges/check-serviceability?pincode=831001", "Pincode lookup"),
    ("GET", "/api/app/version", "App version"),
]

AUTH_ENDPOINTS = [
    # Requires a valid Bearer token — populated at runtime
    ("GET", "/api/cart", "Cart fetch"),
    ("GET", "/api/wishlist", "Wishlist fetch"),
    ("GET", "/api/orders?page=1&limit=10", "Orders - customer"),
    ("GET", "/api/notifications", "Notifications"),
]

ADMIN_ENDPOINTS = [
    # Requires admin token — populated at runtime
    ("GET", "/api/orders?page=1&limit=20", "Orders - admin list"),
    ("GET", "/api/analytics/dashboard", "Analytics dashboard"),
    ("GET", "/api/users?page=1&limit=20", "Users list"),
    ("GET", "/api/products?page=1&limit=20&role=admin", "Products - admin"),
]

# ── Test data ─────────────────────────────────────────────────────────────────
# Override with real credentials via env vars when running auth/admin tests
TEST_CUSTOMER_TOKEN = os.getenv("TEST_CUSTOMER_TOKEN", "")
TEST_ADMIN_TOKEN = os.getenv("TEST_ADMIN_TOKEN", "")
