import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def main():
    f = get_async_session_factory()
    async with f() as s:
        print("Adding columns to sj_orders...")
        await s.execute(text("ALTER TABLE sj_orders ADD COLUMN pending_valet_id varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL"))
        await s.execute(text("ALTER TABLE sj_orders ADD COLUMN valet_assigned_at datetime DEFAULT NULL"))
        await s.execute(text("ALTER TABLE sj_orders ADD COLUMN valet_cascade_count int NOT NULL DEFAULT '0'"))
        await s.execute(text("ALTER TABLE sj_orders ADD COLUMN valet_decline_history longtext COLLATE utf8mb4_unicode_ci"))
        await s.execute(text("ALTER TABLE sj_orders ADD COLUMN is_urgent_delivery tinyint(1) NOT NULL DEFAULT '0'"))
        await s.commit()
        print("Done!")

asyncio.run(main())
