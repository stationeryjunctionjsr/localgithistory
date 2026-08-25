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
        # Check users in SJ_USERS_UAT
        try:
            result = await session.execute(text("SELECT user_id, email, name, role FROM sj_users_uat"))
            rows = result.fetchall()
            print(f"Users in SJ_USERS_UAT: {len(rows)}")
            for row in rows:
                print(f"  ID: {row.user_id}, Email: {row.email}, Name: {row.name}, Role: {row.role}")
        except Exception as e:
            print(f"Error reading sj_users_uat: {e}")

        # Check a few other tables to make sure they are empty
        for t in ["SJ_PRODUCTS_UAT", "SJ_ORDERS_UAT", "SJ_CARTS_UAT"]:
            try:
                res = await session.execute(text(f"SELECT COUNT(*) FROM {t}"))
                cnt = res.scalar()
                print(f"Count in {t}: {cnt}")
            except Exception as e:
                print(f"Error reading {t}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
