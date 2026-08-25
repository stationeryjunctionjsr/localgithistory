import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from app.config.database import get_async_session_factory
from sqlalchemy import text


async def main():
    factory = get_async_session_factory()
    if not factory:
        print("DATABASE_URL not set")
        return

    async with factory() as session:
        # Get all user tables
        result = await session.execute(text("SELECT table_name FROM user_tables ORDER BY table_name"))
        tables = [row[0] for row in result.fetchall()]
        print(f"Total tables: {len(tables)}")

        for t in tables:
            # Get row count
            try:
                count_res = await session.execute(text(f"SELECT COUNT(*) FROM {t}"))
                count = count_res.scalar()
                print(f"Table: {t:30} Rows: {count}")
            except Exception as e:
                print(f"Table: {t:30} Error counting: {e}")


if __name__ == "__main__":
    asyncio.run(main())
