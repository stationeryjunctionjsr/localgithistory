
import asyncio
from sqlalchemy import text
from app.db.mysql_flat_base_dao import get_async_session_factory

async def debug():
    factory = get_async_session_factory()
    async with factory() as session:
        result = await session.execute(text("SELECT id, extra_data FROM sj_coupons WHERE id=56"))
        row = result.fetchone()
        if row:
            print("Row:", row.id, repr(row.extra_data))
        else:
            print("Row not found")

asyncio.run(debug())

