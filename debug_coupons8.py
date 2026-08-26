
import asyncio
from sqlalchemy import text
from app.db.mysql_flat_base_dao import get_async_session_factory

async def debug():
    factory = get_async_session_factory()
    async with factory() as session:
        result = await session.execute(text("SELECT id, is_active, extra_data FROM sj_coupons"))
        rows = result.fetchall()
        for row in rows:
            print("Row:", row.id, row.is_active, type(row.is_active), row.extra_data, type(row.extra_data))

asyncio.run(debug())

