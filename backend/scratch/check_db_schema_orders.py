import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def main():
    f = get_async_session_factory()
    if not f:
        print("No DB connection")
        return
    async with f() as s:
        res = await s.execute(text("SHOW COLUMNS FROM sj_orders"))
        cols = [r[0] for r in res.fetchall()]
        print('valet_cascade_count in sj_orders:', 'valet_cascade_count' in cols)
        print('is_urgent_delivery in sj_orders:', 'is_urgent_delivery' in cols)
        print('pending_valet_id in sj_orders:', 'pending_valet_id' in cols)

asyncio.run(main())
