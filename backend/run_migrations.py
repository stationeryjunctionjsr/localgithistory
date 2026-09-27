import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def run_migrations():
    factory = get_async_session_factory()
    
    # 2. Create analytics sessions table
    create_sql = """
    CREATE TABLE IF NOT EXISTS `sj_analytics_sessions` (
        `id` int NOT NULL AUTO_INCREMENT,
        `session_id` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
        `user_id` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        `is_returning` tinyint(1) DEFAULT '0',
        `source` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        `os` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        `browser` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        `ip_address` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        `device_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        `start_time` datetime NOT NULL,
        `end_time` datetime NOT NULL,
        `time_spent_seconds` int NOT NULL DEFAULT '0',
        PRIMARY KEY (`id`),
        UNIQUE KEY `uq_analytics_session_id` (`session_id`),
        KEY `ix_analytics_sessions_user` (`user_id`),
        KEY `ix_analytics_sessions_start` (`start_time`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    async with factory() as session:
        try:
            await session.execute(text(create_sql))
            print("Successfully created sj_analytics_sessions table.")
        except Exception as e:
            print(f"Error creating table: {e}")
            
        await session.commit()

asyncio.run(run_migrations())
