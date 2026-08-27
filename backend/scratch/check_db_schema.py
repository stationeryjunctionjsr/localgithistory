import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def main():
    factory = get_async_session_factory()
    if not factory:
        print("No DB connection")
        return
    async with factory() as session:
        result = await session.execute(text("SHOW COLUMNS FROM sj_return_requests"))
        for row in result.fetchall():
            print(f"{row[0]}: {row[1]}")

asyncio.run(main())
