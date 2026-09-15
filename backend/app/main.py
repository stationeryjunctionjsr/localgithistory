import asyncio
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables first before importing settings and logger
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded

from app.config.settings import settings
from app.utils.logger import logger, request_id_var

# ── Sentry error tracking ─────────────────────────────────────────────────────
# Initialise only when SENTRY_DSN is provided; completely inert otherwise.
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

_sentry_dsn = os.getenv("SENTRY_DSN", "")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        environment=settings.environment,
        # Capture 100% of errors; tune traces_sample_rate for performance monitoring
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        integrations=[
            StarletteIntegration(transaction_style="url"),
            FastApiIntegration(transaction_style="url"),
        ],
        # Don't send PII (user emails / IPs) by default
        send_default_pii=False,
    )
    logger.info("Sentry initialised (environment=%s)", settings.environment)
else:
    logger.debug("SENTRY_DSN not set — Sentry disabled")


# Held open for the process lifetime to keep the OS scheduler-election lock.
# Never close this — closing it releases the lock.
_SCHEDULER_LOCK_FD = None

# ── SINGLE-VM SCHEDULER ELECTION (file-lock) ─────────────────────────────────
# Keeps exactly one uvicorn worker running the scheduler within this VM.
#
# WHEN SCALING TO MULTIPLE VMs — replace this entire block:
#   1. Delete _try_acquire_scheduler_lock() below and _SCHEDULER_LOCK_FD above.
#   2. Remove the `_is_scheduler_worker` guard in lifespan() below.
#   3. In scheduler.py, uncomment start_recommendation_scheduler_multi_vm()
#      and call it instead of start_recommendation_scheduler().
#      (Full migration steps are documented at the top of scheduler.py.)
# ─────────────────────────────────────────────────────────────────────────────
def _try_acquire_scheduler_lock() -> bool:
    """Elect exactly one uvicorn worker as the scheduler using an OS file lock.

    With ``uvicorn --workers N`` all N worker processes import and execute
    ``lifespan``.  Without a guard every worker starts its own
    ``AsyncIOScheduler``, causing every job to run N times per tick.

    Strategy: the first worker to open and ``flock(LOCK_EX | LOCK_NB)``
    ``/tmp/sj_scheduler.lock`` wins.  Subsequent workers get ``EWOULDBLOCK``
    and skip scheduler startup entirely.  The winning fd is stored in
    ``_SCHEDULER_LOCK_FD`` (module-level) so it is never GC'd — closing the fd
    would silently release the lock.

    Falls back to ``True`` on non-POSIX platforms (Windows dev box) where
    ``fcntl`` is unavailable, so local ``uvicorn app.main:app`` (single worker)
    keeps working.
    """
    global _SCHEDULER_LOCK_FD
    try:
        import fcntl

        lock_path = "/tmp/sj_scheduler.lock"
        fd = open(lock_path, "w")  # noqa: WPS515 — intentionally kept open
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Write PID for observability (e.g. ``cat /tmp/sj_scheduler.lock``)
        fd.write(str(os.getpid()))
        fd.flush()
        _SCHEDULER_LOCK_FD = fd  # prevent garbage collection / lock release
        logger.info("Scheduler election won by PID %d", os.getpid())
        return True
    except ImportError:
        # Windows / non-POSIX: single-worker dev mode, always run scheduler
        return True
    except (OSError, IOError):
        # Another worker already holds the lock
        logger.info("Scheduler election lost (PID %d) — scheduler will not start in this worker", os.getpid())
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — replaces deprecated @app.on_event('startup')."""
    logger.info("Application starting up...")
    await initialize_data_dir()

    # ── Scheduler election ────────────────────────────────────────────────────
    # Only the winning worker starts in-process schedulers.  The OS file lock
    # (held for the process lifetime) prevents the other N-1 workers from
    # starting duplicate schedulers.
    _is_scheduler_worker = _try_acquire_scheduler_lock()

    # Scheduled notification job
    if _is_scheduler_worker:
        try:
            from app.jobs.scheduled_notifications import start_scheduled_notification_job

            start_scheduled_notification_job()
        except Exception as e:
            logger.warning("Could not start scheduled notification job: %s", e)

    # Recommendation scheduler (trending + customer favourites)
    if _is_scheduler_worker:
        try:
            from app.jobs.scheduler import start_recommendation_scheduler

            start_recommendation_scheduler()
        except Exception as e:
            logger.warning("Could not start recommendation scheduler: %s", e)

    # Seed system customer segments (deferred 30 s to avoid cold-start DB contention)
    try:
        from app.routers.customer_segments import seed_system_segments

        async def _deferred_segment_seed():
            await asyncio.sleep(30)
            await seed_system_segments()

        asyncio.create_task(_deferred_segment_seed())
    except Exception as e:
        logger.warning("Could not submit seed customer segments task: %s", e)

    # Ensure required tables exist — gather so failures surface as warnings, not silent drops
    try:
        from app.repositories.stock_reservation_repository import stock_reservation_repository
        from app.repositories.product_notification_repository import product_notification_repository
        from app.repositories.product_review_repository import product_review_repository
        from app.repositories.review_classification_repository import review_classification_repository
        from app.repositories.bundle_repository import bundle_repository
        from app.repositories.return_request_repository import return_request_repository

        results = await asyncio.gather(
            stock_reservation_repository.ensure_table_exists(),
            product_notification_repository.ensure_table_exists(),
            product_review_repository.ensure_table_exists(),
            review_classification_repository.ensure_table_exists(),
            bundle_repository.ensure_table_exists(),
            return_request_repository.ensure_table_columns(),
            return_exceptions=True,
        )
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning("ensure_table_exists[%d] failed: %s", i, r)
    except Exception as e:
        logger.warning("Could not ensure required tables: %s", e)

    # Periodic stock reservation cleanup (every 60 s)
    async def _stock_cleanup_loop():
        while True:
            try:
                await stock_reservation_repository.cleanup_expired()
            except Exception as e:
                logger.error("Error in stock reservation cleanup: %s", e)
            await asyncio.sleep(60)

    asyncio.create_task(_stock_cleanup_loop())
    logger.info("Stock reservation cleanup task started")

    # Pre-warm DB connection pool + critical caches (deferred 5 s)
    async def _warm_critical_caches():
        await asyncio.sleep(5)
        try:
            from app.config.database import get_async_session_factory, use_oracle

            if use_oracle():
                factory = get_async_session_factory()
                if factory:
                    from sqlalchemy import text

                    async def warm_conn():
                        async with factory() as session:
                            await session.execute(text("SELECT 1 FROM DUAL"))

                    # Warm ALL pool slots (pool_size + max_overflow) so no real
                    # user request ever pays the connection-open penalty.
                    # Reads the same env vars as database.py to stay in sync.
                    import os as _os
                    _pool_size = int(_os.getenv("DB_POOL_SIZE", 5))
                    _max_overflow = int(_os.getenv("DB_MAX_OVERFLOW", 2))
                    _total_slots = _pool_size + _max_overflow
                    await asyncio.gather(*[warm_conn() for _ in range(_total_slots)])
                    logger.info("DB connection pool pre-warmed (%d slots)", _total_slots)

            from starlette.responses import Response as _WarmupResponse
            from app.routers.products import get_public_products, get_public_product

            await get_public_products(
                response=_WarmupResponse(),
                category=None,
                categories=None,
                subCategory=None,
                search=None,
                brand=None,
                collection=None,
                popularity=None,
                minDiscount=None,
                minPrice=None,
                maxPrice=None,
                availability=None,
                page=1,
                limit=50,
                role="customer",
                categoryTag=None,
                sort=None,
                includeFacets=True,
                skinny=False,
            )
            await get_public_products(
                response=_WarmupResponse(),
                category=None,
                categories=None,
                subCategory=None,
                search="test",
                brand=None,
                collection=None,
                popularity=None,
                minDiscount=None,
                minPrice=None,
                maxPrice=None,
                availability=None,
                page=1,
                limit=50,
                role="customer",
                categoryTag=None,
                sort=None,
                includeFacets=False,
                skinny=True,
            )
            # Warm up first product detail if possible
            products_res = await get_public_products(
                response=_WarmupResponse(),
                category=None,
                categories=None,
                subCategory=None,
                search=None,
                brand=None,
                collection=None,
                popularity=None,
                minDiscount=None,
                minPrice=None,
                maxPrice=None,
                availability=None,
                page=1,
                limit=1,
                role="customer",
                categoryTag=None,
                sort=None,
                includeFacets=False,
                skinny=True,
            )
            try:
                products_list = products_res.products if products_res.products is not None else []
                if products_list:
                    # In PaginatedProductResponse, products is a list of objects.
                    p0 = products_list[0]
                    p0_id = p0.id
                    if p0_id:
                        await get_public_product(str(p0_id), role="customer", response=_WarmupResponse())
            except Exception as e:
                logger.warning("Failed to warm up get_public_product: %s", e)

            from app.routers.banners import get_public_banners

            await get_public_banners(
                position=None,
                targetAudience=None,
                pageType=None,
                pageId=None,
                userRole="guest",
            )
            from app.routers.categories import get_public_categories

            await get_public_categories(forHomepage=False)
            from app.routers.brands import get_public_brands

            await get_public_brands(forHomepage=False)

            try:
                from app.routers.recommendations import get_recommendations

                await get_recommendations(current_user=None)
            except Exception as re:
                logger.warning("Failed to warm up recommendations: %s", re)

            try:
                from app.routers.delivery_charges import check_serviceability

                await check_serviceability("110001")
            except Exception as e:
                logger.warning("Failed to warm up check-serviceability: %s", e)

            logger.info("Critical API caches pre-warmed")
        except Exception as e:
            logger.warning("Cache warm-up incomplete: %s", e)

    asyncio.create_task(_warm_critical_caches())

    # Auto-create DB indexes (idempotent)
    async def _ensure_indexes():
        try:
            from app.scripts.create_indexes import create_indexes

            await create_indexes()
        except Exception as e:
            logger.warning("Could not create DB indexes: %s", e)

    asyncio.create_task(_ensure_indexes())

    yield  # ← application runs here

    # Shutdown — nothing needed currently; add cleanup here if required
    logger.info("Application shutting down")


app = FastAPI(title="Stationery Junction API", version="1.0.0", lifespan=lifespan)

# Setup Rate Limiting
from slowapi.middleware import SlowAPIMiddleware

from app.utils.limiter import limiter

app.state.limiter = limiter


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429, content={"detail": "Too many requests. Please try again later.", "code": "RATE_LIMIT_EXCEEDED"}
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

origins = settings.allowed_origins_list
if not origins:
    if settings.is_production:
        logger.error("ALLOWED_ORIGINS is not set in production! CORS will block all requests.")
        origins = []
    else:
        logger.warning("ALLOWED_ORIGINS not set; defaulting to http://localhost:3000 in non-production.")
        origins = ["http://localhost:3000"]


# Unified request middleware — combines correlation-ID, maintenance check, timing,
# and secure headers into ONE middleware to eliminate Starlette call_next thread hops
# that cause severe latency under concurrent requests.
import logging as _logging

SLOW_REQUEST_THRESHOLD_MS = settings.slow_request_threshold_ms


@app.middleware("http")
async def unified_request_middleware(request: Request, call_next):
    from app.utils.maintenance import (
        is_maintenance_active,
        is_maintenance_allowlisted,
        maintenance_blocked_payload,
    )

    # Maintenance gate
    if is_maintenance_active() and not is_maintenance_allowlisted(request.url.path):
        return JSONResponse(status_code=503, content=maintenance_blocked_payload())

    # Correlation ID
    req_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    token = request_id_var.set(req_id)

    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)

    duration_ms = (time.perf_counter() - start) * 1000

    # Secure headers
    response.headers["X-Request-Id"] = req_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self), payment=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob: https://*.oraclecloud.com https://maps.googleapis.com https://maps.gstatic.com; "
        "connect-src 'self' https://api.msg91.com https://maps.googleapis.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    # Timing log
    level = _logging.WARNING if duration_ms > SLOW_REQUEST_THRESHOLD_MS else _logging.INFO
    client = request.client.host if request.client else "-"
    logger.log(
        level, "%s %s -> %s in %.0fms [%s]", request.method, request.url.path, response.status_code, duration_ms, client
    )

    return response


# Serve static files (if public directory exists)
# Note: Static files are now in server/public for JavaScript version
# For Python version, create public directory if needed
public_dir = Path(__file__).parent.parent / "public"
if public_dir.exists():
    app.mount("/public", StaticFiles(directory=str(public_dir)), name="public")

# Serve uploaded images
uploads_dir = Path(__file__).parent.parent / "uploads"
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Initialize data directory
import json

from app.config.database import use_oracle
from app.repositories.session_repository import session_repository
from app.utils.auth import ERR_SESSION_REVOKED, verify_token
from app.utils.device import parse_device
from app.utils.file_storage import DATA_DIR, ensure_data_dir


async def initialize_data_dir():
    if use_oracle():
        logger.info("Oracle DB enabled; skipping file-based storage initialization")
        return
    ensure_data_dir()
    files = [
        "users.json",
        "products.json",
        "orders.json",
        "carts.json",
        "wishlists.json",
        "coupons.json",
        "banners.json",
        "brands.json",
        "categories.json",
        "deliveryCharges.json",
        "deliveryChargeDefaults.json",
        "orderFeedback.json",
        "contacts.json",
        "supportTickets.json",
        "tracking.json",
        "savedForLater.json",
        "payments.json",
        "featureFlags.json",
        "notifications.json",
        "categoryTags.json",
        "pushNotifications.json",
        "deviceSubscriptions.json",
        "sessions.json",
        "activities.json",
        "promoStrips.json",
        "collections.json",
        "schemes.json",
        "google_reviews.json",
        "customerSegments.json",
        "referralSettings.json",
        "returnSettings.json",
        "returnRequests.json",
        "ads.json",
        "ad_events.json",
        "productNotifications.json",
        "productReviews.json",
        "reviewClassifications.json",
        "bundles.json",
        "commissionSettings.json",
        "valetAvailability.json",
    ]
    for file in files:
        file_path = DATA_DIR / file
        if not file_path.exists():
            file_path.write_text(json.dumps([], indent=2), encoding="utf-8")

    # Initialize uploads directories
    from app.config.settings import settings

    env = settings.environment.lower()
    if env == "production":
        env_folder = "SJ_PROD"
    elif env == "uat":
        env_folder = "SJ_UAT"
    else:
        env_folder = "SJ_LOCAL"

    uploads_dir = Path(__file__).parent.parent / "uploads" / env_folder
    category_uploads_dir = uploads_dir / "categories"
    product_uploads_dir = uploads_dir / "products"
    brand_uploads_dir = uploads_dir / "brands"
    invoices_uploads_dir = uploads_dir / "invoices"

    category_uploads_dir.mkdir(parents=True, exist_ok=True)
    product_uploads_dir.mkdir(parents=True, exist_ok=True)
    brand_uploads_dir.mkdir(parents=True, exist_ok=True)
    invoices_uploads_dir.mkdir(parents=True, exist_ok=True)

    logger.info("File-based storage initialized")


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Our team has been notified.",
            "code": "INTERNAL_SERVER_ERROR",
        },
    )


# Import and include routers
from app.routers import (
    activity,
    ads,
    analytics,
    auth,
    banners,
    brands,
    bundles,
    cart,
    categories,
    category_tags,
    collections,
    contacts,
    coupons,
    delivery_charges,
    delivery_slots,
    delivery_zones,
    feature_flags,
    google_reviews,
    health,
    media,
    notifications,
    order_feedback,
    orders,
    page_info,
    payments,
    products,
    promo_strips,
    push_notifications,
    recommendations,
    return_settings,
    returns,
    reviews,
    schemes,
    support_tickets,
    tracking,
    upi,
    users,
    version,
    wishlist,
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(coupons.router, prefix="/api/coupons", tags=["coupons"])
app.include_router(banners.router, prefix="/api/banners", tags=["banners"])
app.include_router(brands.router, prefix="/api/brands", tags=["brands"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(upi.router, prefix="/api/upi", tags=["upi"])
app.include_router(delivery_zones.router, prefix="/api/delivery-zones", tags=["delivery-zones"])
app.include_router(delivery_charges.router, prefix="/api/delivery-charges", tags=["delivery-charges"])
app.include_router(delivery_slots.router, prefix="/api/delivery-slots", tags=["delivery-slots"])
app.include_router(order_feedback.router, prefix="/api/order-feedback", tags=["order-feedback"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(support_tickets.router, prefix="/api/support-tickets", tags=["support-tickets"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["tracking"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(wishlist.router, prefix="/api/wishlist", tags=["wishlist"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(feature_flags.router, prefix="/api/feature-flags", tags=["feature-flags"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(category_tags.router, prefix="/api/category-tags", tags=["category-tags"])
app.include_router(promo_strips.router, prefix="/api/promo-strips", tags=["promo-strips"])
app.include_router(page_info.router, prefix="/api/page-info", tags=["page-info"])
app.include_router(collections.router, prefix="/api/collections", tags=["collections"])
app.include_router(schemes.router, prefix="/api/schemes", tags=["schemes"])

from app.routers import coach_marks

app.include_router(coach_marks.router, prefix="/api/coach-marks", tags=["coach-marks"])
app.include_router(push_notifications.router, prefix="/api/push-notifications", tags=["push-notifications"])
from app.routers import search_tags

app.include_router(search_tags.router, prefix="/api/search-tags", tags=["search-tags"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(version.router, prefix="/api/app", tags=["app"])
app.include_router(activity.router, prefix="/api/activity", tags=["activity"])
app.include_router(media.router, prefix="/api", tags=["media"])
app.include_router(google_reviews.router, prefix="/api/google-reviews", tags=["google-reviews"])
from app.routers import customer_segments, pincodes, referrals

app.include_router(pincodes.router, prefix="/api/pincodes", tags=["pincodes"])
app.include_router(customer_segments.router, prefix="/api/customer-segments", tags=["customer-segments"])
app.include_router(referrals.router, prefix="/api/referrals", tags=["referrals"])
app.include_router(returns.router, prefix="/api/returns", tags=["returns"])
app.include_router(return_settings.router, prefix="/api/settings/returns", tags=["return-settings"])
app.include_router(ads.router, prefix="/api/ads", tags=["ads"])
app.include_router(health.router, prefix="/api", tags=["health"])
from app.routers import content_pages

app.include_router(content_pages.router, prefix="/api/content", tags=["content-pages"])
app.include_router(bundles.router, prefix="/api/bundles", tags=["bundles"])

from app.routers import commission, valet_payout, valet_availability, availability_requests

app.include_router(commission.router, prefix="/api/commission", tags=["commission"])
app.include_router(valet_payout.router, prefix="/api/valet-payout", tags=["valet-payout"])
app.include_router(valet_availability.router, prefix="/api/valet-availability", tags=["valet-availability"])
app.include_router(availability_requests.router, prefix="/api/availability-requests", tags=["availability_requests"])

# Prometheus metrics disabled — its middleware adds a call_next layer per request
# which doubles latency under concurrency. Re-enable only in production behind
# a reverse proxy that handles concurrent connection queuing.
# try:
#     Instrumentator().instrument(app).expose(app)
# except Exception as e:
#     logger.warning(f"Failed to start prometheus instrumentator: {e}")

# In-memory session last touch times to debounce database updates.
_session_last_touch = {}


# Middleware to update session activity and device info
@app.middleware("http")
async def touch_session_middleware(request: Request, call_next):
    global _session_last_touch
    from app.utils.cookies import get_token_from_request

    token = get_token_from_request(request)
    if not token:
        return await call_next(request)
    try:
        # Lightweight JWT decode just to extract session ID — no DB calls.
        # Full verification happens in get_current_user() inside the route.
        from jose import jwt as jose_jwt

        payload = jose_jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
        session_id = payload.get("sessionId")
        if session_id:
            device = parse_device(request, default_type="web")
            now = time.time()
            cache_key = (session_id, device)
            last_touch = _session_last_touch.get(cache_key, 0)

            # Only update the DB if 60 seconds have elapsed since the last touch
            if now - last_touch > 60:
                asyncio.create_task(session_repository.touch(session_id, device))
                _session_last_touch[cache_key] = now

                # Cleanup cache if it grows too large to prevent memory leaks
                if len(_session_last_touch) > 10000:
                    _session_last_touch = {k: t for k, t in _session_last_touch.items() if now - t <= 60}
    except Exception as e:
        if isinstance(e, HTTPException) and isinstance(e.detail, dict) and e.detail.get("code") == ERR_SESSION_REVOKED:
            return JSONResponse(status_code=401, content=e.detail)
        # Silently ignore — route's get_current_user() will handle real auth errors
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    return {"message": "Stationery Junction API", "version": "1.0.0"}


# Outermost Middleware (CORS) - MUST BE THE LAST MIDDLEWARE ADDED
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-Id", "Accept"],
)

if __name__ == "__main__":
    import asyncio
    import sys

    import uvicorn

    # Fix for asyncio ProactorEventLoop error on Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
