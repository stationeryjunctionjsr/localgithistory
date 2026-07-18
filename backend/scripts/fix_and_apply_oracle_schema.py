import asyncio
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Add backend root so app imports work
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory

CORE_TABLES = [
    "sj_users",
    "sj_categories",
    "sj_brands",
    "sj_products",
    "sj_orders",
    "sj_order_items",
    "sj_carts",
    "sj_wishlists",
    "sj_sessions",
    "sj_coupons",
    "sj_banners",
]


def get_statements(file_path: Path):
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return []
    content = file_path.read_text(encoding="utf-8")

    # Pre-process JSON -> CLOB for 19c
    content = re.sub(r"\s+JSON(\s*|,)", " CLOB\\1", content, flags=re.I)

    # Split by semicolon.
    # This is naive but works for standard SQL files without procedural blocks.
    raw_statements = content.split(";")
    cleaned = []
    for s in raw_statements:
        # Remove comments
        lines = [line for line in s.splitlines() if not line.strip().startswith("--")]
        stmt = "\n".join(lines).strip()
        if stmt:
            cleaned.append(stmt)
    return cleaned


async def main():
    factory = get_async_session_factory()
    if not factory:
        print("No database connection factory. Check .env")
        return

    print("Extracting statements from schema files...")
    all_stmts = get_statements(backend_root / "scripts" / "schema_oracle.sql")
    typed_stmts = get_statements(backend_root / "scripts" / "schema_oracle_relational_json.sql")

    print(f"  Extracted {len(all_stmts)} from schema_oracle.sql")
    print(f"  Extracted {len(typed_stmts)} from schema_oracle_typed_parent_only.sql")

    core_final = []
    for stmt in all_stmts:
        if "sj_" not in stmt.lower():
            continue

        # Match CREATE TABLE sj_... or CREATE INDEX ... ON sj_...
        match = re.search(r"CREATE\s+(TABLE|INDEX|UNIQUE INDEX)\s+([\w\$]+)", stmt, re.I)
        if match:
            obj_name = match.group(2).lower()
            if match.group(1).upper() == "TABLE":
                if obj_name in CORE_TABLES:
                    core_final.append(stmt)
            else:
                on_match = re.search(r"ON\s+([\w\$]+)", stmt, re.I)
                if on_match and on_match.group(1).lower() in CORE_TABLES:
                    core_final.append(stmt)
        elif "ALTER TABLE" in stmt.upper():
            match_alter = re.search(r"ALTER TABLE\s+([\w\$]+)", stmt, re.I)
            if match_alter and match_alter.group(1).lower() in CORE_TABLES:
                core_final.append(stmt)

    print(f"  Filtered {len(core_final)} core statements.")

    async with factory() as session:
        # Check current tables
        result = await session.execute(text("SELECT table_name FROM user_tables WHERE table_name LIKE 'SJ_%'"))
        existing_tables = [row[0] for row in result.all()]
        print(f"Found {len(existing_tables)} existing sj_ tables.")

        # 1. Drop
        for table in existing_tables:
            print(f"Dropping {table}...")
            try:
                await session.execute(text(f"DROP TABLE {table} CASCADE CONSTRAINTS"))
            except Exception as e:
                print(f"  Error: {e}")

        # 2. Apply Core
        print(f"Applying {len(core_final)} core statements...")
        for stmt in core_final:
            try:
                await session.execute(text(stmt))
            except Exception as e:
                print(f"  Error on: {stmt[:100]}...\n  {e}")

        # 3. Apply Typed
        print(f"Applying {len(typed_stmts)} typed statements...")
        for stmt in typed_stmts:
            try:
                await session.execute(text(stmt))
            except Exception as e:
                print(f"  Error on: {stmt[:100]}...\n  {e}")

        print("Committing Changes...")
        await session.commit()

    print("Schema Application Finished Successfully.")


if __name__ == "__main__":
    asyncio.run(main())
