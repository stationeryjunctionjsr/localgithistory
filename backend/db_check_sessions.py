import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def run_query():
    factory = get_async_session_factory()
    async with factory() as session:
        res = await session.execute(text("DESCRIBE sj_analytics_sessions;"))
        columns = res.fetchall()
        print("--- sj_analytics_sessions columns ---")
        for col in columns:
            print(f"{col[0]} - {col[1]}")

asyncio.run(run_query())
