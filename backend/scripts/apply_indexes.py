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

async def run():
    factory = get_async_session_factory()
    if not factory:
        print("ERROR: DATABASE_URL not set in environment.")
        return

    migration_file = Path("scripts/add_indexes_migration.sql")
    if not migration_file.exists():
        print(f"ERROR: Migration file {migration_file} does not exist.")
        return

    with open(migration_file, "r") as f:
        sql_content = f.read()

    # Strip comments first
    lines = []
    for line in sql_content.splitlines():
        # Strip -- comment if present
        clean_line = line.split("--")[0].strip()
        if clean_line:
            lines.append(clean_line)
    sql_clean = " ".join(lines)
    statements = [stmt.strip() for stmt in sql_clean.split(";") if stmt.strip()]

    print("=" * 60)
    print("Applying sj_products database indexes...")
    print("=" * 60)

    async with factory() as session:
        for stmt in statements:
            if not stmt:
                continue
            
            print(f"Executing: {stmt}")
            try:
                await session.execute(text(stmt))
                await session.commit()
                print("  Success! [OK]")
            except Exception as e:
                await session.rollback()
                err_msg = str(e)
                if "ORA-00955" in err_msg or "name is already used" in err_msg:
                    print("  Skipped: Index name already exists (ORA-00955) [OK]")
                elif "ORA-01408" in err_msg or "such column list already indexed" in err_msg:
                    print("  Skipped: Columns already indexed (ORA-01408) [OK]")
                else:
                    print(f"  FAILED: {err_msg}")

    print("=" * 60)
    print("Migration complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run())
