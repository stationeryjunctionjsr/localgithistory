"""
Scheduled job: compute Trending Now (search-to-sale journey, 7 days, top 5 per subcategory)
and write to trending_cache.json. Run at 12 PM and 12 AM IST.
"""

import asyncio
from datetime import datetime, timezone

from app.repositories.recommendation_repository import (
    _write_trending_cache,
    recommendation_repository,
)
from app.utils.logger import logger


async def run_trending_job():
    """Compute trending for customer and wholesaler (no cache), write cache."""
    try:
        now = datetime.now(timezone.utc)
        customer_ids = await recommendation_repository.get_trending_by_conversion(
            "customer",
            days=7,
            min_search_count=10,
            top_per_subcategory=5,
            exclude_product_ids=set(),
            use_cache=False,
        )
        wholesaler_ids = await recommendation_repository.get_trending_by_conversion(
            "wholesaler",
            days=7,
            min_search_count=10,
            top_per_subcategory=5,
            exclude_product_ids=set(),
            use_cache=False,
        )
        updated_at = now.isoformat()
        _write_trending_cache(
            {
                "customer": {"product_ids": customer_ids, "updated_at": updated_at},
                "wholesaler": {"product_ids": wholesaler_ids, "updated_at": updated_at},
            }
        )
        logger.info(
            "[Trending job] Updated at %s: customer=%s, wholesaler=%s",
            updated_at,
            len(customer_ids),
            len(wholesaler_ids),
        )
    except Exception as e:
        logger.error("[Trending job] Error: %s", str(e), exc_info=True)
        raise


def run_trending_job_sync():
    """Entry point for scheduler (sync)."""
    asyncio.run(run_trending_job())


if __name__ == "__main__":
    run_trending_job_sync()
