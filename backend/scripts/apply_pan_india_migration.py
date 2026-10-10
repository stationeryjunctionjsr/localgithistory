import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.config.database import get_async_session_factory
from sqlalchemy import text

async def run_migration():
    factory = get_async_session_factory()
    if not factory:
        print("Error: Could not obtain database session factory.")
        return

    columns_to_add = [
        # (table, column, definition)
        ("sj_orders", "fulfillment_type", "VARCHAR(20) NOT NULL DEFAULT 'hyperlocal'"),
        ("sj_orders", "courier_partner", "VARCHAR(64) DEFAULT NULL"),
        ("sj_orders", "tracking_id", "VARCHAR(64) DEFAULT NULL"),
        ("sj_orders", "awb_code", "VARCHAR(64) DEFAULT NULL"),
        ("sj_orders", "shipping_label_url", "VARCHAR(500) DEFAULT NULL"),
        ("sj_orders", "estimated_delivery_date", "DATETIME DEFAULT NULL"),
        
        ("sj_sub_orders", "fulfillment_type", "VARCHAR(20) NOT NULL DEFAULT 'hyperlocal'"),
        ("sj_sub_orders", "courier_partner", "VARCHAR(64) DEFAULT NULL"),
        ("sj_sub_orders", "tracking_id", "VARCHAR(64) DEFAULT NULL"),
        ("sj_sub_orders", "awb_code", "VARCHAR(64) DEFAULT NULL"),
        
        ("sj_products", "weight_grams", "INT NOT NULL DEFAULT 200"),
        ("sj_products", "length_cm", "DECIMAL(6,2) DEFAULT NULL"),
        ("sj_products", "width_cm", "DECIMAL(6,2) DEFAULT NULL"),
        ("sj_products", "height_cm", "DECIMAL(6,2) DEFAULT NULL"),
        ("sj_products", "hsn_code", "VARCHAR(16) DEFAULT NULL"),
        
        ("sj_delivery_charge_defaults", "courier_base_charge", "DECIMAL(10,2) NOT NULL DEFAULT 60.00"),
        ("sj_delivery_charge_defaults", "courier_free_threshold", "DECIMAL(10,2) NOT NULL DEFAULT 499.00")
    ]

    async with factory() as session:
        print("Checking database columns and applying updates...\n")
        for table, col, col_def in columns_to_add:
            # Check if column already exists
            check_sql = text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_NAME = :tbl AND COLUMN_NAME = :col AND TABLE_SCHEMA = DATABASE()"
            )
            res = await session.execute(check_sql, {"tbl": table, "col": col})
            exists = res.scalar() > 0

            if exists:
                print(f"[-] {table}.{col} already exists. Skipping.")
            else:
                print(f"[+] Adding {table}.{col} ...")
                alter_sql = text(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
                await session.execute(alter_sql)
                await session.commit()
                print(f"    -> Successfully added {table}.{col}!")

        print("\nAll Pan-India columns verified and migrated successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
