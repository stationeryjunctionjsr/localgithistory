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
        # Query foreign keys
        print("FOREIGN KEYS:")
        result = await session.execute(text("""
            SELECT a.table_name, a.constraint_name, a.column_name, 
                   c_pk.table_name r_table_name, c_pk.constraint_name r_constraint_name
            FROM user_cons_columns a
            JOIN user_constraints c ON a.constraint_name = c.constraint_name
            JOIN user_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
            WHERE c.constraint_type = 'R'
            ORDER BY a.table_name
        """))
        for row in result.fetchall():
            print(f"  {row.table_name}.{row.column_name} ({row.constraint_name}) -> {row.r_table_name} ({row.r_constraint_name})")

        # Query indexes
        print("\nINDEXES:")
        result = await session.execute(text("""
            SELECT table_name, index_name, uniqueness
            FROM user_indexes
            WHERE table_name LIKE 'SJ_%'
            ORDER BY table_name, index_name
        """))
        for row in result.fetchall():
            print(f"  {row.table_name}: {row.index_name} ({row.uniqueness})")

if __name__ == "__main__":
    asyncio.run(main())
