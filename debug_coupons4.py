
import asyncio
from sqlalchemy import text
from app.db.mysql_flat_base_dao import get_async_session_factory

async def debug():
    factory = get_async_session_factory()
    async with factory() as session:
        result = await session.execute(text("SELECT * FROM sj_coupons"))
        rows = result.fetchall()
        print("Rows:", len(rows))

asyncio.run(debug())

