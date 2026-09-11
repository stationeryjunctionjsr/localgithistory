import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend root so app imports work
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc

OBSOLETE_FLAGS = [
    "enable_coupons",
    "enable_delivery_charge_update",
    "enable_quantity_discounts",
    "enable_quantity_discount",
    "enable_tracking",
    "enable_banners",
    "enable_customer_support",
    "enable_credit_orders",
    "enable_gst_calculation",
    "retail_enable_credit",
]

NEW_FLAGS = [
    {
        "flag_id": "retail_enable_cod",
        "name": "Retail COD",
        "description": "Enable Cash on Delivery for Retail customers",
        "enabled": 1,
        "category": "payments",
    },
    {
        "flag_id": "retail_enable_upi",
        "name": "Retail UPI",
        "description": "Enable UPI payment for Retail customers",
        "enabled": 1,
        "category": "payments",
    },
    {
        "flag_id": "retail_enable_gst",
        "name": "Retail GST",
        "description": "Enable GST calculation for Retail customers",
        "enabled": 1,
        "category": "payments",
    },
    {
        "flag_id": "wholesale_enable_cod",
        "name": "Wholesale COD",
        "description": "Enable Cash on Delivery for Wholesale customers",
        "enabled": 1,
        "category": "payments",
    },
    {
        "flag_id": "wholesale_enable_upi",
        "name": "Wholesale UPI",
        "description": "Enable UPI payment for Wholesale customers",
        "enabled": 1,
        "category": "payments",
    },
    {
        "flag_id": "wholesale_enable_credit",
        "name": "Wholesale Credit",
        "description": "Enable Credit orders for Wholesale customers",
        "enabled": 1,
        "category": "payments",
    },
    {
        "flag_id": "wholesale_enable_gst",
        "name": "Wholesale GST",
        "description": "Enable GST calculation for Wholesale customers",
        "enabled": 1,
        "category": "payments",
    },
]


async def main():
    print("Connecting to Oracle...")
    factory = get_async_session_factory()
    if not factory:
        print("ERROR: DATABASE_URL not set")
        return

    now = now_utc()

    async with factory() as session:
        # 1. Clean up obsolete flags
        for flag_id in OBSOLETE_FLAGS:
            print(f"Removing obsolete flag: {flag_id}")
            await session.execute(text("DELETE FROM sj_feature_flags WHERE flag_id = :flag_id"), {"flag_id": flag_id})

        # 2. Add or update segment-based flags
        for f in NEW_FLAGS:
            # Check if it already exists
            r = await session.execute(
                text("SELECT id FROM sj_feature_flags WHERE flag_id = :flag_id"), {"flag_id": f["flag_id"]}
            )
            exists = r.fetchone()
            if exists:
                print(f"Updating flag: {f['flag_id']}")
                await session.execute(
                    text("""
                        UPDATE sj_feature_flags SET
                            name = :name,
                            description = :description,
                            category = :category,
                            updated_at = :updated_at
                        WHERE flag_id = :flag_id
                    """),
                    {
                        "flag_id": f["flag_id"],
                        "name": f["name"],
                        "description": f["description"],
                        "category": f["category"],
                        "updated_at": now,
                    },
                )
            else:
                print(f"Creating new flag: {f['flag_id']}")
                await session.execute(
                    text("""
                        INSERT INTO sj_feature_flags (
                            flag_id, name, description, enabled, category, created_at, updated_at
                        ) VALUES (
                            :flag_id, :name, :description, :enabled, :category, :created_at, :updated_at
                        )
                    """),
                    {
                        "flag_id": f["flag_id"],
                        "name": f["name"],
                        "description": f["description"],
                        "enabled": f["enabled"],
                        "category": f["category"],
                        "created_at": now,
                        "updated_at": now,
                    },
                )

        await session.commit()
        print("Migration and seeding complete!")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
