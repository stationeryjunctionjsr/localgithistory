import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path and load env
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory

async def check_coupons():
    factory = get_async_session_factory()
    if not factory:
        print("No DATABASE_URL found.")
        return

    async with factory() as session:
        print("Dumping existing rows in SJ_COUPONS...")
        r = await session.execute(text("SELECT * FROM SJ_COUPONS"))
        rows = r.fetchall()
        print(f"Total coupons: {len(rows)}")
        for row in rows:
            print(dict(row._mapping))

if __name__ == "__main__":
    asyncio.run(check_coupons())
