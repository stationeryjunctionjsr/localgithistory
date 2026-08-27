import asyncio
import os
from datetime import datetime, timedelta

from app.services.email_service import email_service
from app.services.report_service import report_service
from app.utils.logger import logger


async def run_daily_search_report_job():
    """
    Job that runs daily to generate and send the search report.
    """
    logger.info("[%s] Starting daily search report job...", datetime.now())

    try:
        # Generate report for yesterday
        yesterday = datetime.now() - timedelta(days=1)
        report_path = await report_service.generate_daily_search_report(yesterday)

        if not os.path.exists(report_path):
            logger.warning("[%s] Report generation failed or no data found.", datetime.now())
            return

        # Send email to the configured admin emails
        to_emails = email_service.admin_emails
        if not to_emails:
            logger.warning("[%s] No admin emails configured. Skipping.", datetime.now())
            return

        subject = f"Daily Search Keywords Report - {yesterday.strftime('%Y-%m-%d')}"
        body = f"Please find attached the daily search keywords report for {yesterday.strftime('%Y-%m-%d')}."

        success = email_service.send_email_with_attachment(to_emails, subject, body, report_path)

        if success:
            logger.info("[%s] Daily search report sent successfully to %s", datetime.now(), ", ".join(to_emails))
        else:
            logger.error("[%s] Failed to send daily search report email.", datetime.now())

    except Exception as e:
        logger.error("[%s] Error in daily search report job: %s", datetime.now(), str(e), exc_info=True)


if __name__ == "__main__":
    # Manual test run
    asyncio.run(run_daily_search_report_job())
