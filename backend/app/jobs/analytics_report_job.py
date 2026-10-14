"""
Scheduled job: pre-compute reporting and analytics dashboard data
at 6 AM, 12 Noon, 6 PM, and 12 AM IST daily.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from app.utils.logger import logger

IST = timezone(timedelta(hours=5, minutes=30))


async def run_analytics_report_job():
    """Compute and cache stale analytics reports for the dashboard."""
    try:
        from app.repositories.analytics_repository import analytics_repository
        now_ist = datetime.now(IST)
        ist_formatted = now_ist.strftime("%d %b %Y, %I:%M %p IST")
        logger.info("[Analytics Report Job] Starting pre-computation at %s", ist_formatted)
        await analytics_repository.precompute_dashboard_reports(ist_formatted)
        logger.info("[Analytics Report Job] Finished pre-computation successfully")
    except Exception as e:
        logger.error("[Analytics Report Job] Error precomputing reports: %s", str(e), exc_info=True)


def run_analytics_report_job_sync():
    """Sync entry point for scheduler invocation if needed."""
    asyncio.run(run_analytics_report_job())


if __name__ == "__main__":
    run_analytics_report_job_sync()
