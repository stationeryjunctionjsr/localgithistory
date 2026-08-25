"""
Stationery Junction — Locust Load Test Entry Point
===================================================

Usage (from backend/ directory):

  # Interactive Web UI (recommended for first run):
  locust -f load_tests/locustfile.py --host http://localhost:8000

  # Headless — run 50 users for 2 minutes, save report:
  locust -f load_tests/locustfile.py \
    --host http://localhost:8000 \
    --headless -u 50 -r 5 -t 2m \
    --html load_tests/reports/load_report.html \
    --csv load_tests/reports/load

  # Use run_load_tests.py for automated sequential profiles.

User mix (reflects real-world traffic distribution):
  - GuestUser    60 % weight  — browsing without login
  - CustomerUser 30 % weight  — authenticated shopping
  - AdminUser    10 % weight  — admin panel operations

Environment Variables:
  TEST_CUSTOMER_TOKEN  — Bearer token for a customer account
  TEST_ADMIN_TOKEN     — Bearer token for an admin account
  LOAD_TEST_BASE_URL   — Override API base URL (default: http://localhost:8000)
"""

import os
import sys

# Allow imports from load_tests package when running from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from locust import HttpUser, between, tag

from load_tests.scenarios.admin_scenario import AdminOperations
from load_tests.scenarios.customer_scenario import CustomerShopping
from load_tests.scenarios.guest_scenario import GuestBrowsing


# ── User Classes ──────────────────────────────────────────────────────────────


class GuestUser(HttpUser):
    """
    Unauthenticated visitor — no credentials required.
    Represents ~60 % of real traffic (browsing, search).
    Think time: 0.5–2 s (fast mobile-ish browsing).
    """

    weight = 6
    wait_time = between(0.5, 2.0)
    tasks = [GuestBrowsing]

    def on_start(self):
        # Guest users don't need to log in
        pass


class CustomerUser(HttpUser):
    """
    Logged-in customer — uses TEST_CUSTOMER_TOKEN.
    Represents ~30 % of real traffic.
    Think time: 1–3 s (browsing + adding to cart).
    """

    weight = 3
    wait_time = between(1.0, 3.0)
    tasks = [CustomerShopping]

    def on_start(self):
        pass


class AdminUser(HttpUser):
    """
    Admin panel user — uses TEST_ADMIN_TOKEN.
    Represents ~10 % of real traffic.
    Think time: 0.3–1 s (fast dashboard polling).
    """

    weight = 1
    wait_time = between(0.3, 1.0)
    tasks = [AdminOperations]

    def on_start(self):
        pass
