import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def run():
    factory = get_async_session_factory()
    async with factory() as session:
        await session.execute(text("ALTER TABLE sj_analytics_sessions DROP COLUMN is_returning;"))
        print("Dropped is_returning from sj_analytics_sessions")
        await session.commit()

asyncio.run(run())
