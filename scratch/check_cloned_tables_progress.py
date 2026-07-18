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
        result = await session.execute(text("SELECT table_name FROM user_tables WHERE table_name LIKE '%_UAT' ORDER BY table_name"))
        tables = [row[0] for row in result.fetchall()]
        print(f"Total cloned UAT tables found: {len(tables)}")
        for t in tables:
            print(f"  - {t}")

if __name__ == "__main__":
    asyncio.run(main())
