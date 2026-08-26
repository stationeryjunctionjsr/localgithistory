import socket
import sys
import asyncio

# The IPv4 getaddrinfo patch was removed as it caused asyncio.gather to hang during DB connection pool initialization.

# Use WindowsSelectorEventLoopPolicy on Windows to prevent async SSL "event loop closed" errors.
# The policy is deprecated in Python 3.14 and will be removed in 3.16; on those versions the
# default ProactorEventLoop no longer has the SSL issues, so falling back silently is safe.
if sys.platform == "win32":
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except AttributeError:
            pass  # Removed in Python 3.16+; ProactorEventLoop is reliable by then

import uvicorn
import os
from dotenv import load_dotenv

# Load env file based on APP_ENV or ENVIRONMENT, defaulting to standard .env
app_env = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "")).lower()
if app_env == "uat":
    print("Loading UAT environment config (.env.uat)...")
    load_dotenv(".env.uat")
elif app_env == "production":
    print("Loading Production environment config (.env.production)...")
    load_dotenv(".env.production")
elif app_env == "qa":
    print("Loading QA environment config (.env.qa)...")
    load_dotenv(".env.qa")
else:
    load_dotenv()

if __name__ == "__main__":
    from app.main import app

    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}...")

    # Auto-whitelist IP for Oracle Autonomous DB
    import subprocess

    try:
        print("Checking/updating IP whitelist for Oracle DB...", flush=True)
        subprocess.run([sys.executable, "whitelist_current_ip.py"], check=True)
    except Exception as e:
        print(f"Warning: Failed to auto-whitelist IP (this may cause connection errors): {e}")

    workers = int(os.getenv("WORKERS", 4))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=workers,
        loop="asyncio",
        # Raise the TCP accept-queue beyond the OS default (128 on many Linux/Docker
        # base images). On production Linux this prevents connection drops during
        # sudden traffic bursts before Uvicorn can accept() them.
        backlog=2048,
    )
