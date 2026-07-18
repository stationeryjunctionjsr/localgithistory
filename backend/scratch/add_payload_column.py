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

async def alter_table():
    factory = get_async_session_factory()
    if not factory:
        print("No DATABASE_URL found.")
        return

    async with factory() as session:
        print("Adding 'payload' CLOB column to SJ_COUPONS table...")
        try:
            await session.execute(text("ALTER TABLE SJ_COUPONS ADD payload CLOB"))
            await session.commit()
            print("Successfully added payload column.")
        except Exception as e:
            print(f"Error or column already exists: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(alter_table())
