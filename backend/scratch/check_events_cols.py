import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory

async def check():
    factory = get_async_session_factory()
    if not factory:
        print("No DB connection")
        return
    async with factory() as session:
        for t in ["SJ_EVENTS", "SJ_EVENTS_UAT", "SJ_TRACKING", "SJ_TRACKING_UAT"]:
            res = await session.execute(text(f"SELECT column_name, data_type FROM user_tab_cols WHERE table_name = '{t}'"))
            cols = res.fetchall()
            print(f"\nColumns for {t}:")
            for c in cols:
                print(f"  - {c[0]} ({c[1]})")

if __name__ == "__main__":
    asyncio.run(check())
