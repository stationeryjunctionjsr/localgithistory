import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def run():
    factory = get_async_session_factory()
    async with factory() as session:
        for table in ["sj_sessions", "sj_session_devices"]:
            print(f"\n--- {table} ---")
            res = await session.execute(text(f"DESCRIBE {table};"))
            for row in res.fetchall():
                print(f"  {row[0]:35} {row[1]}")

asyncio.run(run())
