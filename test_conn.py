
import asyncio
from sqlalchemy import text
from app.db.mysql_flat_base_dao import get_async_session_factory

async def test():
    factory = get_async_session_factory()
    try:
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        print("Connected!")
    except Exception as e:
        print("Error:", e)

asyncio.run(test())

