import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def main():
    f = get_async_session_factory()
    async with f() as s:
        res = await s.execute(text("SHOW COLUMNS FROM sj_orders"))
        cols = [r[0] for r in res.fetchall()]
        check = ["pending_valet_id","valet_assigned_at","valet_cascade_count","valet_decline_history","is_urgent_delivery"]
        for c in check:
            print(f"{c}: {'EXISTS' if c in cols else 'MISSING'}")

asyncio.run(main())
