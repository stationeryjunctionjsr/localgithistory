import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory

async def main():
    factory = get_async_session_factory()
    if not factory:
        print("DATABASE_URL not set")
        return

    async with factory() as session:
        result = await session.execute(text("SELECT index_name, table_name FROM user_indexes WHERE table_name LIKE '%_UAT' ORDER BY table_name"))
        indexes = result.fetchall()
        print(f"Total cloned UAT indexes found: {len(indexes)}")
        for idx in indexes:
            print(f"  - Index: {idx[0]} on table {idx[1]}")

if __name__ == "__main__":
    asyncio.run(main())
