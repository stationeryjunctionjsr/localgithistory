"""
Migration Script: Update Customer IDs for All Users

This script ensures all users have a customerId:
- Super admin gets customerId = 1
- All other users get incremental customerId starting from 2

Run this script once to update existing users:
python -m app.scripts.update_customer_ids
"""

import asyncio
import logging
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.utils.file_storage import FileStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_customer_ids():
    storage = FileStorage("users")

    try:
        logger.info("Starting customerId migration...")

        # Get all users
        users = await storage.findAll()
        logger.info("Found %s users", len(users))

        # Find super admin
        super_admin = next((u for u in users if u.get("role") == "super_admin"), None)

        # Sort users: super admin first, then by creation date
        def sort_key(user):
            # Super admin first
            if user.role == "super_admin":
                return (0, user.get("createdAt", ""))
            # Then by creation date
            return (1, user.get("createdAt", ""))

        sorted_users = sorted(users, key=sort_key)

        customer_id = 1
        updated_count = 0

        for user in sorted_users:
            # Skip if already has correct customerId
            if user.user_id_formatted == customer_id:
                logger.info(
                    "User %s (%s) already has customerId %s",
                    user.id,
                    user.name,
                    customer_id,
                )
                customer_id += 1
                continue

            # Update user with customerId
            await storage.update(user.id, {"customerId": customer_id})
            logger.info(
                "Updated user %s (%s, role: %s) with customerId %s",
                user.id,
                user.name,
                user.role,
                customer_id,
            )
            updated_count += 1
            customer_id += 1

        logger.info("Migration complete! Updated %s users.", updated_count)
        if super_admin:
            logger.info("Super admin customerId: %s", super_admin.get("customerId", 1))

    except Exception as error:
        logger.error("Migration failed: %s", str(error), exc_info=True)
        sys.exit(1)


# Run migration
if __name__ == "__main__":
    asyncio.run(update_customer_ids())
    logger.info("Script completed successfully")
