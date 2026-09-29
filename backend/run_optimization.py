import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def run_migrations():
    factory = get_async_session_factory()
    
    # 1. Add columns to sj_analytics_sessions
    add_sql = """
    ALTER TABLE sj_analytics_sessions
    ADD COLUMN campaign varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    ADD COLUMN device_os_version varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    ADD COLUMN device_model varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    ADD COLUMN device_app_version varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    """
    
    # 2. Drop columns from sj_tracking
    drop_sql = """
    ALTER TABLE sj_tracking
    DROP COLUMN os,
    DROP COLUMN browser,
    DROP COLUMN ip_address,
    DROP COLUMN is_returning,
    DROP COLUMN campaign,
    DROP COLUMN device_type,
    DROP COLUMN device_os_version,
    DROP COLUMN device_model,
    DROP COLUMN device_app_version;
    """
    
    async with factory() as session:
        try:
            await session.execute(text(add_sql))
            print("Successfully added columns to sj_analytics_sessions.")
        except Exception as e:
            print(f"Error adding columns: {e}")
            
        try:
            await session.execute(text(drop_sql))
            print("Successfully dropped columns from sj_tracking.")
        except Exception as e:
            print(f"Error dropping columns: {e}")
            
        await session.commit()

asyncio.run(run_migrations())
