"""
Business metrics for Prometheus.

Counters are always incremented even when the /metrics endpoint is disabled —
they accumulate in-process memory and are ready to scrape the moment you
expose the endpoint.

To expose /metrics:
  1. Un-comment the Instrumentator block in main.py (lines ~544-550).
  2. Add an nginx / OCI load-balancer rule so /metrics and /internal/metrics
     are only reachable from your Prometheus scraper IP, not the public internet.
  3. Set PROMETHEUS_ENABLED=true in .env.

Internal endpoint (no extra middleware latency):
  GET /internal/metrics  — returns Prometheus text format.
  Only responds to 127.0.0.1 or the IP in PROMETHEUS_SCRAPER_IP env var.
"""

import os
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Request
from fastapi.responses import Response

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

ORDERS_CREATED = Counter(
    "sj_orders_created_total",
    "Total number of orders successfully created",
    ["payment_method"],  # label: upi, cod, credit, online
)

ORDERS_FAILED = Counter(
    "sj_orders_failed_total",
    "Total number of order creation failures",
    ["reason"],  # label: stock_unavailable, payment_error, validation_error, unknown
)

ORDER_GMV = Counter(
    "sj_order_gmv_rupees_total",
    "Gross merchandise value of successfully created orders in INR (paise not used)",
    ["payment_method"],
)

PAYMENT_FAILURES = Counter(
    "sj_payment_failures_total",
    "Total payment failures by method",
    ["method"],  # label: upi, cod, credit, online
)

UPI_CONFIRMATIONS = Counter(
    "sj_upi_confirmations_total",
    "UPI payments confirmed by the user ('I Have Paid' pressed)",
)

COUPON_REDEMPTIONS = Counter(
    "sj_coupon_redemptions_total",
    "Total coupon redemptions (coupon applied at order creation)",
    ["coupon_type"],  # label: flat, percent, free_shipping, etc.
)

OTP_REQUESTS = Counter(
    "sj_otp_requests_total",
    "Total OTP send requests",
    ["status"],  # label: sent, rate_limited, error
)

LOGIN_LOCKOUTS = Counter(
    "sj_login_lockouts_total",
    "Total login lockout events (per-phone brute-force threshold exceeded)",
)

# ---------------------------------------------------------------------------
# Protected /internal/metrics endpoint
# ---------------------------------------------------------------------------

router = APIRouter()

_SCRAPER_IP = os.getenv("PROMETHEUS_SCRAPER_IP", "127.0.0.1")


@router.get("/internal/metrics", include_in_schema=False)
async def internal_metrics(request: Request):
    """Prometheus text-format scrape endpoint.

    Only accessible from localhost or the configured PROMETHEUS_SCRAPER_IP.
    Mount this router in main.py BEFORE the public routes.
    """
    client_ip = request.client.host if request.client else ""
    if client_ip not in ("127.0.0.1", "::1", _SCRAPER_IP):
        # Return 404 (not 403) so the endpoint doesn't reveal its existence
        from fastapi.responses import Response as _R
        return _R(status_code=404)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
