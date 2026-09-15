"""
Scheduled job to check and send scheduled push notifications
Runs every minute to check for notifications that should be sent
"""

import asyncio
from datetime import datetime, timezone

from app.repositories.push_notification_repository import push_notification_repository
from app.services.push_notification_service import push_notification_service
from app.utils.logger import logger


async def check_scheduled_notifications():
    """Check for scheduled notifications that should be sent now"""
    try:
        now = datetime.now(timezone.utc)

        # Find all scheduled notifications
        all_notifications = await push_notification_repository.findAll()
        scheduled_notifications = [n for n in all_notifications if (n["status"] if "status" in n else None) == "scheduled"]

        notifications_to_send = []
        for notification in scheduled_notifications:
            scheduled_for = notification["scheduledFor"] if "scheduledFor" in notification else None
            if scheduled_for:
                try:
                    # Parse the scheduled date
                    if isinstance(scheduled_for, str):
                        # Handle ISO format strings
                        scheduled_str = scheduled_for.replace("Z", "+00:00")
                        scheduled_date = datetime.fromisoformat(scheduled_str)
                        if scheduled_date.tzinfo is None:
                            scheduled_date = scheduled_date.replace(tzinfo=timezone.utc)
                    else:
                        continue

                    # Send if scheduled time has passed
                    if scheduled_date <= now:
                        notifications_to_send.append(notification)
                except Exception as e:
                    logger.warning(
                        "Error parsing scheduled date for notification %s: %s",
                        notification["_id"] if "_id" in notification else None,
                        str(e),
                    )
                    continue

        # Send each scheduled notification
        for notification in notifications_to_send:
            try:
                logger.info(
                    "Sending scheduled notification: %s - %s",
                    notification["_id"] if "_id" in notification else None,
                    notification["title"] if "title" in notification else None,
                )

                # Send the notification
                await push_notification_service.send_to_all_devices(notification)

                # Update status to published
                await push_notification_repository.update(notification["_id"], {"status": "published"})

                logger.info("Successfully sent scheduled notification: %s", notification["_id"] if "_id" in notification else None)
            except Exception as error:
                logger.error(
                    "Error sending scheduled notification %s: %s",
                    notification["_id"] if "_id" in notification else None,
                    str(error),
                    exc_info=True,
                )
                # Don't update status if sending failed - will retry on next run
    except Exception as error:
        logger.error("Error checking scheduled notifications: %s", str(error), exc_info=True)


async def run_scheduled_job():
    """Run the scheduled notification check in a loop"""
    while True:
        try:
            await check_scheduled_notifications()
        except Exception as e:
            logger.error("Error in scheduled notification job: %s", str(e), exc_info=True)

        # Wait 60 seconds before next check
        await asyncio.sleep(60)


def start_scheduled_notification_job():
    """Start the scheduled notification job in a background task"""
    logger.info("Starting scheduled notification job (runs every minute)...")

    # Run immediately on startup to catch any missed notifications
    asyncio.create_task(check_scheduled_notifications())

    # Then run every minute
    asyncio.create_task(run_scheduled_job())

    logger.info("Scheduled notification job started")
