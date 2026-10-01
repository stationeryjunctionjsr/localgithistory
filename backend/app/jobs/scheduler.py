"""
Scheduler for recommendation jobs (IST).
- Trending: 12:00 AM and 12:00 PM IST daily.
- Customer Favourites: 12:00 AM IST daily.

Single-VM mode (active):
    AsyncIOScheduler with no job store — pure in-memory.
    A file lock in main.py (_try_acquire_scheduler_lock) ensures exactly one
    uvicorn worker starts the scheduler.  Zero DB overhead on every tick.

Multi-VM mode (commented out below — see start_recommendation_scheduler_multi_vm):
    AsyncIOScheduler backed by APScheduler's SQLAlchemyJobStore pointing at
    the shared MySQL database.  APScheduler uses SELECT … FOR UPDATE SKIP LOCKED
    internally so only one worker across ALL VMs fires each job.
    To activate: uncomment start_recommendation_scheduler_multi_vm and follow
    the three-step migration guide in its docstring.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.jobs.customer_favourites_job import run_customer_favourites_job
from app.jobs.search_report_job import run_daily_search_report_job
from app.jobs.trending_job import run_trending_job
from app.utils.logger import logger

IST = "Asia/Kolkata"


async def _google_reviews_job():
    from app.repositories.google_review_repository import google_review_repository

    try:
        await google_review_repository.fetch_and_update()
        logger.info("Google reviews refreshed successfully via scheduled job")
    except Exception as e:
        logger.error("Error in google_reviews_job: %s", str(e), exc_info=True)


async def _resource_monitoring_job():
    from app.config.database import get_async_session_factory
    from app.utils.error_handler import check_db_usage, check_system_resources

    # Check CPU/Mem (Sync)
    check_system_resources()

    # Check DB (Async)
    try:
        session_factory = get_async_session_factory()
        if session_factory:
            async with session_factory() as session:
                await check_db_usage(session)
    except Exception as e:
        logger.error("Error in DB resource monitoring: %s", str(e), exc_info=True)


def start_recommendation_scheduler():
    """Start the background scheduler (call from app startup).

    This must only be called by the elected scheduler worker (see main.py's
    _try_acquire_scheduler_lock). All jobs run without coordination overhead
    because the file-lock election guarantees exactly one process runs this.
    """
    scheduler = AsyncIOScheduler(timezone=IST)
    # Trending: 12:00 AM and 12:00 PM IST
    scheduler.add_job(
        run_trending_job,
        CronTrigger(hour="0,12", minute=0, timezone=IST),
        id="trending_job",
    )
    # Customer Favourites: 12:00 AM IST
    scheduler.add_job(
        run_customer_favourites_job,
        CronTrigger(hour=0, minute=0, timezone=IST),
        id="customer_favourites_job",
    )
    # Google Reviews: 12:00 AM IST
    scheduler.add_job(
        _google_reviews_job,
        CronTrigger(hour=0, minute=0, timezone=IST),
        id="google_reviews_job",
    )
    # Customer Segments Refresh: 12:00 AM IST
    from app.jobs.customer_segments_job import run_customer_segments_refresh_job

    scheduler.add_job(
        run_customer_segments_refresh_job,
        CronTrigger(hour=0, minute=0, timezone=IST),
        id="customer_segments_refresh_job",
    )
    # Daily Search Keywords Report: 12:00 AM IST
    scheduler.add_job(
        run_daily_search_report_job,
        CronTrigger(hour=0, minute=0, timezone=IST),
        id="daily_search_report_job",
    )
    # Daily Events Reconciler & Sync: DISABLED — mobile events now write directly
    # to sj_tracking in real-time via /api/analytics/events. No batch sync needed.
    # from app.jobs.events_sync_job import run_events_sync_job_async
    # scheduler.add_job(
    #     run_events_sync_job_async,
    #     CronTrigger(hour=0, minute=0, timezone=IST),
    #     id="daily_events_sync_job",
    # )
    # Resource Monitoring: Every 30 minutes
    scheduler.add_job(
        _resource_monitoring_job,
        "interval",
        minutes=30,
        id="resource_monitoring_job",
    )
    # Valet timeout + auto-cascade: Every 1 minute
    from app.jobs.valet_timeout_job import run_valet_timeout_job
    scheduler.add_job(
        run_valet_timeout_job,
        "interval",
        minutes=1,
        id="valet_timeout_job",
        max_instances=1,
        coalesce=True,
    )
    # Seller Availability Tick: Every 15 minutes
    from app.routers.seller_availability import tick_availability_statuses

    scheduler.add_job(
        tick_availability_statuses,
        "interval",
        minutes=15,
        id="tick_availability_statuses_job",
    )
    scheduler.start()
    logger.info(
        "Recommendation scheduler started (IST): trending 12 AM/PM, favorites 12 AM, google reviews 12 AM"
    )

# ── MULTI-VM SCHEDULER (commented out — activate when scaling to multiple VMs) ──
#
# HOW TO ACTIVATE (3 steps):
#
#   Step 1 — Replace the call in main.py:
#       Change:  start_recommendation_scheduler()
#       To:      start_recommendation_scheduler_multi_vm()
#
#   Step 2 — Remove the file-lock election from main.py:
#       Delete the _try_acquire_scheduler_lock() call and the
#       `if _is_scheduler_worker:` guards.  All workers can now call
#       start_recommendation_scheduler_multi_vm() freely — APScheduler's
#       SQLAlchemyJobStore handles exclusive execution internally via
#       SELECT … FOR UPDATE SKIP LOCKED on the sj_apscheduler_jobs table.
#
#   Step 3 — Remove the _try_acquire_scheduler_lock function and the
#       _SCHEDULER_LOCK_FD module-level variable from main.py entirely.
#
# WHY THIS WORKS ACROSS VMs:
#   All VMs share the same MySQL database.  APScheduler stores every job's
#   next_run_time in sj_apscheduler_jobs.  When the trigger fires, each
#   worker races to acquire a row-level lock on that job row.  The winner
#   executes; all others skip.  This is enforced by the database engine,
#   not by clocks or cooldowns, so it is exact.
#
# PREREQUISITES:
#   - pymysql is already in requirements.txt (needed for the sync URL).
#   - No new infrastructure — uses the existing MySQL instance.
#   - APScheduler 3.x is already in requirements.txt (APScheduler==3.11.2).
#
# def start_recommendation_scheduler_multi_vm():
#     """Start the distributed scheduler backed by MySQL (SQLAlchemyJobStore).
#
#     Safe to call in every uvicorn worker on every VM.  APScheduler's job
#     store guarantees exactly-once execution per scheduled tick across all
#     workers and VMs via database-level row locking.
#     """
#     from app.config.database import DATABASE_URL
#     from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
#
#     # SQLAlchemyJobStore requires a *synchronous* driver.
#     # pymysql is already installed (see requirements.txt).
#     # DATABASE_URL uses aiomysql (async) — swap the driver prefix only.
#     if not DATABASE_URL:
#         logger.error("Cannot start multi-VM scheduler: DATABASE_URL is not set.")
#         return
#
#     sync_db_url = DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")
#
#     scheduler = AsyncIOScheduler(
#         jobstores={
#             "default": SQLAlchemyJobStore(
#                 url=sync_db_url,
#                 tablename="sj_apscheduler_jobs",  # sj_ prefix matches project convention
#             )
#         },
#         job_defaults={
#             # coalesce: if a job missed several runs (e.g. VM was down), run it
#             # only once when the VM comes back up rather than catching up on all
#             # missed fires.
#             "coalesce": True,
#             # max_instances: never run the same job concurrently in one worker.
#             # Combined with coalesce this means exactly one execution per tick
#             # across all workers and VMs.
#             "max_instances": 1,
#             # misfire_grace_time: if a worker wakes up and finds a job's
#             # scheduled time was up to 120 s ago, still run it (e.g. after a
#             # brief restart). Set to None to always run regardless of delay.
#             "misfire_grace_time": 120,
#         },
#         timezone=IST,
#     )
#
#     # Trending: 12:00 AM and 12:00 PM IST
#     scheduler.add_job(
#         run_trending_job,
#         CronTrigger(hour="0,12", minute=0, timezone=IST),
#         id="trending_job",
#         replace_existing=True,  # safe to call on every worker restart
#     )
#     # Customer Favourites: 12:00 AM IST
#     scheduler.add_job(
#         run_customer_favourites_job,
#         CronTrigger(hour=0, minute=0, timezone=IST),
#         id="customer_favourites_job",
#         replace_existing=True,
#     )
#     # Google Reviews: 12:00 AM IST
#     scheduler.add_job(
#         _google_reviews_job,
#         CronTrigger(hour=0, minute=0, timezone=IST),
#         id="google_reviews_job",
#         replace_existing=True,
#     )
#     # Customer Segments Refresh: 12:00 AM IST
#     from app.jobs.customer_segments_job import run_customer_segments_refresh_job
#
#     scheduler.add_job(
#         run_customer_segments_refresh_job,
#         CronTrigger(hour=0, minute=0, timezone=IST),
#         id="customer_segments_refresh_job",
#         replace_existing=True,
#     )
#     # Daily Search Keywords Report: 12:00 AM IST
#     scheduler.add_job(
#         run_daily_search_report_job,
#         CronTrigger(hour=0, minute=0, timezone=IST),
#         id="daily_search_report_job",
#         replace_existing=True,
#     )
#     # Daily Events Reconciler & Sync: 12:00 AM IST
#     from app.jobs.events_sync_job import run_events_sync_job_async
#
#     scheduler.add_job(
#         run_events_sync_job_async,
#         CronTrigger(hour=0, minute=0, timezone=IST),
#         id="daily_events_sync_job",
#         replace_existing=True,
#     )
#     # Resource Monitoring: Every 30 minutes
#     # NOTE: Unlike other jobs, resource monitoring is intentionally NOT
#     # deduplicated — each VM should monitor its own CPU/memory independently.
#     # Do not add it to this distributed scheduler; keep it in a separate
#     # per-worker BackgroundScheduler or asyncio task if you need it.
#
#     scheduler.start()
#
#     logger.info(
#         "Multi-VM scheduler started (SQLAlchemyJobStore / MySQL): "
#         "trending 12 AM/PM, favorites 12 AM, google reviews 12 AM, events sync 12 AM"
#     )
#
# ─────────────────────────────────────────────────────────────────────────────────
