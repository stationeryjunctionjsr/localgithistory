import asyncio
from app.config.database import get_async_session_factory
from sqlalchemy import text


async def test():
    print("Connecting...")
    factory = get_async_session_factory()
    async with factory() as session:
        res = await session.execute(text("SHOW TABLES;"))
        print("Tables:", [r[0] for r in res.fetchall()])


asyncio.run(test())
