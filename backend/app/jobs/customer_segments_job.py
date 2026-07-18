import asyncio
import datetime

from app.repositories.customer_segments_repository import customer_segments_repository
from app.routers.customer_segments import FilterCriteria, run_segment_filter
from app.utils.logger import logger


async def run_customer_segments_refresh_job():
    """Daily job to refresh all active customer segments."""
    logger.info("[%s] Starting customer segments refresh job...", datetime.datetime.utcnow().isoformat())

    segments = await customer_segments_repository.get_all()
    active_segments = [s for s in segments if s.get("isActive", True)]

    for segment in active_segments:
        segment_id = segment.get("_id")
        filters = segment.get("filters", {})
        if not segment_id or not filters:
            continue

        logger.info("Refreshing segment: %s (%s)", segment.get("name"), segment_id)
        try:
            role = "customer" if segment.get("type") == "retail" else "wholesaler"
            criteria = FilterCriteria(role=role, **filters)

            users = await run_segment_filter(criteria)
            user_ids = [str(u.get("_id", u.get("id"))) for u in users]

            await customer_segments_repository.update(
                segment_id, {"userIds": user_ids, "lastRefreshedAt": datetime.datetime.utcnow().isoformat()}
            )
        except Exception as e:
            logger.error("Failed to refresh segment %s: %s", segment_id, str(e), exc_info=True)

    logger.info("[%s] Customer segments refresh job completed.", datetime.datetime.utcnow().isoformat())


def run_customer_segments_refresh_job_sync():
    """Sync wrapper for the scheduler."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # If loop is already running, create a task
        asyncio.create_task(run_customer_segments_refresh_job())
    else:
        loop.run_until_complete(run_customer_segments_refresh_job())
