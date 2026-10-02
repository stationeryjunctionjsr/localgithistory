import os
import sys

from slowapi import Limiter
from slowapi.util import get_remote_address

# Disable rate limiting in test environment to avoid hitting limits during automated tests
is_test = (
    "pytest" in sys.modules
    or os.getenv("TESTING", "false").lower() == "true"
    or os.getenv("DISABLE_RATE_LIMIT", "false").lower() == "true"
)

# ── Storage backend ────────────────────────────────────────────────────────────
# With 4 Uvicorn workers each process has its own in-memory counter, so a
# client can make up to 4× the stated rate limit before being blocked.
#
# When REDIS_URL is set, slowapi uses a shared Redis counter — all workers and
# all VMs see the same count, giving exact enforcement of every rate limit.
#
# Current deployment (single VM, no Redis): REDIS_URL is not set, so the
# limiter falls back to in-memory automatically — no change in behaviour.
# To upgrade: add REDIS_URL=redis://<host>:6379 to the environment file.
# The `limits` library (already installed) ships RedisStorage; no extra
# package is needed.
#
# in_memory_fallback_enabled=True means: if Redis becomes temporarily
# unavailable, the limiter degrades to per-process in-memory rather than
# either crashing the app or letting every request through.
# ──────────────────────────────────────────────────────────────────────────────
_redis_url = os.getenv("REDIS_URL", "")

limiter = Limiter(
    key_func=get_remote_address,
    # Catch-all floor for unauthenticated / undecorated endpoints.
    # ≈10 req/s per worker; with up to 4 workers effective throughput for a
    # single client is ~2 400 req/min before any worker blocks the client.
    default_limits=["600/minute"],
    enabled=not is_test,
    storage_uri=_redis_url if _redis_url else None,
    in_memory_fallback_enabled=bool(_redis_url),  # fallback only when Redis is configured
)

# Guard: never allow rate-limit bypass in a deployed environment
_env = os.getenv("ENVIRONMENT", "development").lower()
if _env not in ("development", "local") and os.getenv("DISABLE_RATE_LIMIT", "false").lower() == "true":
    raise RuntimeError(
        f"[SECURITY] DISABLE_RATE_LIMIT=true is not allowed in ENVIRONMENT={_env!r}. "
        "Remove this variable from the server environment before starting."
    )
