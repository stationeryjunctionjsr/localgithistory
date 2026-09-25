import asyncio
import datetime
from datetime import timezone

from app.repositories.customer_segments_repository import customer_segments_repository
from app.routers.customer_segments import FilterCriteria, run_segment_filter
from app.utils.logger import logger


async def run_customer_segments_refresh_job():
    """Daily job to refresh all active customer segments."""
    logger.info("[%s] Starting customer segments refresh job...", datetime.datetime.now(timezone.utc).isoformat())

    segments = await customer_segments_repository.get_all()
    active_segments = [s for s in segments if (s["isActive"] if "isActive" in s else True)]

    for segment in active_segments:
        segment_id = segment["_id"] if "_id" in segment else None
        filters = segment["filters"] if "filters" in segment else {}
        if not segment_id or not filters:
            continue

        logger.info("Refreshing segment: %s (%s)", segment["name"] if "name" in segment else None, segment_id)
        try:
            role = "customer" if (segment["type"] if "type" in segment else None) == "retail" else "wholesaler"
            criteria = FilterCriteria(role=role, **filters)

            users = await run_segment_filter(criteria)
            user_ids = [str(u["_id"] if "_id" in u else (u["id"] if "id" in u else None)) for u in users]

            await customer_segments_repository.update(
                segment_id, {"userIds": user_ids, "lastRefreshedAt": datetime.datetime.now(timezone.utc).isoformat()}
            )
        except Exception as e:
            logger.error("Failed to refresh segment %s: %s", segment_id, str(e), exc_info=True)

    logger.info("[%s] Customer segments refresh job completed.", datetime.datetime.now(timezone.utc).isoformat())


def run_customer_segments_refresh_job_sync():
    """Sync wrapper for the scheduler."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # If loop is already running, create a task
        asyncio.create_task(run_customer_segments_refresh_job())
    else:
        loop.run_until_complete(run_customer_segments_refresh_job())
