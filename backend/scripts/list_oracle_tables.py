import asyncio
import os
import sys
from pathlib import Path

# Add backend root so app imports work
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory


async def list_tables():
    factory = get_async_session_factory()
    if not factory:
        print("No factory")
        return
    async with factory() as session:
        result = await session.execute(text("SELECT table_name FROM user_tables ORDER BY table_name"))
        tables = [row[0] for row in result.all()]
        print("Tables in schema:")
        for table in tables:
            print(f"- {table}")


if __name__ == "__main__":
    asyncio.run(list_tables())
