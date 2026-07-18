import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Load environment BEFORE any app imports
backend_root = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv(dotenv_path=backend_root / ".env")

from sqlalchemy import text
from app.config.database import get_async_session_factory


async def fix_oracle_schema():
    factory = get_async_session_factory()
    if not factory:
        url = os.environ.get("DATABASE_URL")
        print(f"Could not create session factory. DATABASE_URL is: {url}")
        return

    async with factory() as session:
        print("Dropping foreign keys to sj_users(id)...")
        # Find constraint names and drop them
        queries = [
            "ALTER TABLE sj_orders DROP CONSTRAINT fk_sj_orders_user",
            "ALTER TABLE sj_carts DROP CONSTRAINT fk_sj_carts_user",
            "ALTER TABLE sj_wishlists DROP CONSTRAINT fk_sj_wishlists_user",
            "ALTER TABLE sj_sessions DROP CONSTRAINT fk_sj_sessions_user",
        ]
        for q in queries:
            try:
                await session.execute(text(q))
                print(f"  OK: {q}")
            except Exception as e:
                print(f"  SKIPPED: {q} ({e})")

        print("\nCleaning up sj_users columns...")
        try:
            # Oracle 12c+ allows dropping multiple columns, but let's do it step by step
            await session.execute(text("ALTER TABLE sj_users DROP COLUMN user_id"))
            print("  OK: Dropped old user_id column")
        except Exception as e:
            print(f"  SKIPPED: Drop user_id ({e})")

        try:
            await session.execute(text("ALTER TABLE sj_users RENAME COLUMN id TO user_id"))
            print("  OK: Renamed id to user_id")
        except Exception as e:
            print(f"  SKIPPED: Rename id ({e})")

        print("\nRecreating foreign keys to sj_users(user_id)...")
        new_fks = [
            "ALTER TABLE sj_orders ADD CONSTRAINT fk_sj_orders_user FOREIGN KEY (user_id) REFERENCES sj_users (user_id)",
            "ALTER TABLE sj_carts ADD CONSTRAINT fk_sj_carts_user FOREIGN KEY (user_id) REFERENCES sj_users (user_id)",
            "ALTER TABLE sj_wishlists ADD CONSTRAINT fk_sj_wishlists_user FOREIGN KEY (user_id) REFERENCES sj_users (user_id)",
            "ALTER TABLE sj_sessions ADD CONSTRAINT fk_sj_sessions_user FOREIGN KEY (user_id) REFERENCES sj_users (user_id)",
        ]
        for q in new_fks:
            try:
                await session.execute(text(q))
                print(f"  OK: {q}")
            except Exception as e:
                print(f"  ERROR: {q} ({e})")

        await session.commit()
        print("\nSchema updated successfully!")


if __name__ == "__main__":
    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL is missing in environment!")
        sys.exit(1)

    asyncio.run(fix_oracle_schema())
