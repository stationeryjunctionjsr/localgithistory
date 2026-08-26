import asyncio

from app.config.database import get_async_session_factory
from sqlalchemy import text


async def main():
    factory = get_async_session_factory()
    async with factory() as session:
        result = await session.execute(text("DESCRIBE sj_customer_segments"))
        for row in result.fetchall():
            print(row)


asyncio.run(main())
