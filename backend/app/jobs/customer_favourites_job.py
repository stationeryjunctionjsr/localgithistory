"""
Scheduled job: compute Customer Favourites and Business Favourites (top 1 per subcategory by quantity+frequency)
and write to cache. Run at 12 AM IST.
"""

import asyncio

from app.repositories.recommendation_repository import (
    _write_business_favourites_cache,
    _write_customer_favourites_cache,
    get_recommendation_config,
    recommendation_repository,
)
from app.utils.logger import logger


async def run_customer_favourites_job():
    """Compute Customer Favourites (retail) and Business Favourites (wholesaler), write caches."""
    try:
        config = get_recommendation_config()
        seg = config.get("segments", {}).get("guest", {})
        cf_days = seg.get("customer_favourites_days", 60)
        cf_data = await recommendation_repository.compute_customer_favourites_for_cache(days=cf_days)
        _write_customer_favourites_cache(cf_data)
        logger.info("[Customer Favourites job] Updated: %s products", len(cf_data.get("product_ids", [])))

        wh_seg = config.get("segments", {}).get("wholesaler", {})
        bf_days = wh_seg.get("business_favourites_days", wh_seg.get("wholesaler_favourites_days", 60))
        bf_data = await recommendation_repository.compute_business_favourites_for_cache(days=bf_days)
        _write_business_favourites_cache(bf_data)
        logger.info("[Business Favourites job] Updated: %s products", len(bf_data.get("product_ids", [])))
    except Exception as e:
        logger.error("[Favourites job] Error: %s", str(e), exc_info=True)
        raise


def run_customer_favourites_job_sync():
    """Entry point for scheduler (sync)."""
    asyncio.run(run_customer_favourites_job())


if __name__ == "__main__":
    run_customer_favourites_job_sync()
