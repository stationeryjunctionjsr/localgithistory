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
        # Get all user tables
        result = await session.execute(text("SELECT table_name FROM user_tables ORDER BY table_name"))
        tables = [row[0] for row in result.fetchall()]
        print(f"Total tables found in user_tables: {len(tables)}")
        for t in tables:
            print(f"  - {t}")

        # Check if they have identity columns
        print("\nIdentity columns info:")
        result = await session.execute(text("""
            SELECT table_name, column_name, generation_type, identity_options 
            FROM user_tab_identity_cols
            ORDER BY table_name
        """))
        for row in result.fetchall():
            print(f"  {row.table_name}.{row.column_name}: {row.generation_type} {row.identity_options}")

if __name__ == "__main__":
    asyncio.run(main())
