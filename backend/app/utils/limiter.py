import os
import sys

from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared limiter instance
# Disable rate limiting in test environment to avoid hitting limits during automated tests
is_test = (
    "pytest" in sys.modules
    or os.getenv("TESTING", "false").lower() == "true"
    or os.getenv("DISABLE_RATE_LIMIT", "false").lower() == "true"
)
limiter = Limiter(key_func=get_remote_address, default_limits=["100000/minute"], enabled=not is_test)

# Guard: never allow rate-limit bypass in a deployed environment
_env = os.getenv("ENVIRONMENT", "development").lower()
if _env not in ("development", "local") and os.getenv("DISABLE_RATE_LIMIT", "false").lower() == "true":
    raise RuntimeError(
        f"[SECURITY] DISABLE_RATE_LIMIT=true is not allowed in ENVIRONMENT={_env!r}. "
        "Remove this variable from the server environment before starting."
    )
