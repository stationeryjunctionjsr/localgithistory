import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend root so app imports work
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory


async def check_all_tables():
    factory = get_async_session_factory()
    async with factory() as session:
        result = await session.execute(
            text("SELECT owner, table_name FROM all_tables WHERE owner = 'ADMIN' ORDER BY table_name")
        )
        tables = result.all()
        print(f"Tables owned by ADMIN in all_tables:")
        for owner, table in tables:
            print(f"- {owner}.{table}")


if __name__ == "__main__":
    asyncio.run(check_all_tables())
