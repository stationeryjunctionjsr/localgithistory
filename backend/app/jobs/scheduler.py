"""
Scheduler for recommendation jobs (IST).
- Trending: 12:00 AM and 12:00 PM IST daily.
- Customer Favourites: 12:00 AM IST daily.
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
    from app.config.database import get_async_session_factory, use_oracle
    from app.utils.error_handler import check_db_usage, check_system_resources

    # Check CPU/Mem (Sync)
    check_system_resources()

    # Check DB (Async)
    if use_oracle():
        try:
            session_factory = get_async_session_factory()
            if session_factory:
                async with session_factory() as session:
                    await check_db_usage(session)
        except Exception as e:
            # We don't want to log this as CRITICAL to avoid loops if DB is down
            logger.error("Error in DB resource monitoring: %s", str(e), exc_info=True)


def start_recommendation_scheduler():
    """Start the background scheduler (call from app startup)."""
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
    # Daily Events Reconciler & Sync: 12:00 AM IST
    from app.jobs.events_sync_job import run_events_sync_job_async

    scheduler.add_job(
        run_events_sync_job_async,
        CronTrigger(hour=0, minute=0, timezone=IST),
        id="daily_events_sync_job",
    )
    # Resource Monitoring: Every 30 minutes
    scheduler.add_job(
        _resource_monitoring_job,
        "interval",
        minutes=30,
        id="resource_monitoring_job",
    )
    scheduler.start()
    logger.info(
        "Recommendation scheduler started (IST): trending 12 AM/PM, favorites 12 AM, google reviews 12 AM, events sync 12 AM"
    )
