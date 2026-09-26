import asyncio
from app.config.database import get_async_session_factory
from sqlalchemy import text

async def show_cols():
    factory = get_async_session_factory()
    async with factory() as session:
        res = await session.execute(text('SHOW COLUMNS FROM sj_coupons'))
        print([r[0] for r in res.fetchall()])

asyncio.run(show_cols())
