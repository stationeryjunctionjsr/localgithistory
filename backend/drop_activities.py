import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def run():
    factory = get_async_session_factory()
    async with factory() as session:
        await session.execute(text("DROP TABLE IF EXISTS sj_activity_meta;"))
        print("Dropped sj_activity_meta")
        await session.execute(text("DROP TABLE IF EXISTS sj_activities;"))
        print("Dropped sj_activities")
        await session.commit()

asyncio.run(run())
