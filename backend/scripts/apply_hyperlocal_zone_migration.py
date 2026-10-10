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
        ("sj_delivery_zones", "delivery_charge", "DECIMAL(10,2) DEFAULT NULL"),
        ("sj_delivery_zones", "min_cart_value", "DECIMAL(10,2) DEFAULT NULL"),
        ("sj_delivery_zones", "urgent_delivery_charge", "DECIMAL(10,2) DEFAULT NULL"),
        ("sj_delivery_zones", "apply_default_charge", "TINYINT(1) NOT NULL DEFAULT 1"),

        ("sj_delivery_charge_defaults", "hyperlocal_base_charge", "DECIMAL(10,2) NOT NULL DEFAULT 40.00"),
        ("sj_delivery_charge_defaults", "hyperlocal_free_threshold", "DECIMAL(10,2) NOT NULL DEFAULT 300.00"),
        ("sj_delivery_charge_defaults", "hyperlocal_urgent_delivery_charge", "DECIMAL(10,2) DEFAULT 50.00")
    ]

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS sj_delivery_zone_tiers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        parent_id INT NOT NULL COMMENT 'FK to sj_delivery_zones.id',
        min_order_value VARCHAR(255) DEFAULT '0' COMMENT 'Lower bound cart value',
        max_order_value VARCHAR(255) NOT NULL COMMENT 'Upper bound cart value or Infinity',
        charge VARCHAR(255) NOT NULL COMMENT 'Delivery fee for this tier',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_zone_parent (parent_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    async with factory() as session:
        print("1. Checking and adding columns...")
        for table, col, col_def in columns_to_add:
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

        print("\n2. Ensuring child table sj_delivery_zone_tiers exists...")
        await session.execute(text(create_table_sql))
        await session.commit()
        print("[+] Table sj_delivery_zone_tiers verified/created successfully!")

        print("\nAll Hyperlocal Zone Delivery Charge DB changes applied successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
