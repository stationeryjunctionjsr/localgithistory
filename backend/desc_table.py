import asyncio
from app.db.mysql_coupons_dao import get_async_session_factory
from sqlalchemy import text
async def run():
    async with get_async_session_factory()() as session:
        r = await session.execute(text("DESCRIBE sj_coupons"))
        for t in r:
            print(t[0])
asyncio.run(run())
