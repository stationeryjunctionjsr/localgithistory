import asyncio
import datetime
from datetime import timezone

from app.models.daos_flat import CustomerSegmentInternalUpdate
from app.repositories.customer_segments_repository import customer_segments_repository
from app.routers.customer_segments import FilterCriteria, run_segment_filter
from app.utils.logger import logger


async def run_customer_segments_refresh_job():
    """Daily job to refresh all active customer segments."""
    logger.info("[%s] Starting customer segments refresh job...", datetime.datetime.now(timezone.utc).isoformat())

    segments = await customer_segments_repository.get_all()
    active_segments = [s for s in segments if (s.is_active if s.is_active is not None else True)]

    for segment in active_segments:
        segment_id = segment.id
        filters = segment.filters
        if not segment_id or not filters:
            continue

        logger.info("Refreshing segment: %s (%s)", segment.name, segment_id)
        try:
            role = "customer" if segment.type == "retail" else "wholesaler"
            criteria = FilterCriteria(
                role=role,
                minAverageOrderValue=filters.min_average_order_value,
                maxAverageOrderValue=filters.max_average_order_value,
                startDate=filters.start_date,
                endDate=filters.end_date,
                minOrderFrequency=filters.min_order_frequency,
                maxOrderFrequency=filters.max_order_frequency,
                state=filters.state,
                district=filters.district,
                appUser=filters.app_user,
                behavior=filters.behavior,
            )

            user_ids = await run_segment_filter(criteria)

            await customer_segments_repository.update(
                segment_id,
                CustomerSegmentInternalUpdate(
                    user_ids=user_ids,
                    updated_at=datetime.datetime.now(timezone.utc),
                ),
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
