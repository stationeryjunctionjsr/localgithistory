from sqlalchemy import text
from app.config.database import get_async_engine
import asyncio

async def add_columns():
    engine = get_async_engine()
    async with engine.begin() as conn:
        columns = [
            "display_id VARCHAR(100) DEFAULT NULL",
            "bxgy_applies_to_ids JSON DEFAULT NULL",
            "bxgy_discount_type VARCHAR(64) DEFAULT NULL",
            "bxgy_discount_value DECIMAL(10,2) DEFAULT NULL",
            "applicable_item_type VARCHAR(64) DEFAULT NULL",
            "coupon_mode VARCHAR(64) DEFAULT NULL",
            "max_usage_per_user INT DEFAULT NULL",
            "user_usages JSON DEFAULT NULL",
            "user_behavior VARCHAR(128) DEFAULT NULL"
        ]
        
        for col in columns:
            col_name = col.split(" ")[0]
            try:
                await conn.execute(text(f"ALTER TABLE sj_coupons ADD COLUMN {col}"))
                print(f"Added column {col_name}")
            except Exception as e:
                print(f"Error adding {col_name} (might already exist): {e}")

asyncio.run(add_columns())
