import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

TABLES = [
    "sj_orders",
    "sj_return_requests",
    "sj_return_valet_declines",
]

async def main():
    f = get_async_session_factory()
    if not f:
        print("No DB connection")
        return
    async with f() as s:
        # Get all table names
        res = await s.execute(text("SHOW TABLES"))
        all_tables = {r[0] for r in res.fetchall()}
        print("=== TABLE EXISTENCE ===")
        for t in TABLES:
            print(f"  {t}: {'EXISTS' if t in all_tables else 'MISSING'}")

        print("")
        for t in TABLES:
            if t not in all_tables:
                continue
            print(f"=== COLUMNS: {t} ===")
            res2 = await s.execute(text(f"SHOW COLUMNS FROM {t}"))
            for r in res2.fetchall():
                print(f"  {r[0]}: {r[1]}")
            print("")

asyncio.run(main())
