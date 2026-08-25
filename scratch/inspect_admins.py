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
        # Find all users with admin role or email
        result = await session.execute(
            text("""
            SELECT user_id, email, name, role, is_active, approval_status 
            FROM sj_users 
            WHERE LOWER(role) LIKE '%admin%' OR LOWER(email) = 'stationeryjunction.jsr@gmail.com'
        """)
        )
        print("Admins in SJ_USERS:")
        for row in result.fetchall():
            print(
                f"  ID: {row.user_id}, Email: {row.email}, Name: {row.name}, Role: {row.role}, Active: {row.is_active}, Status: {row.approval_status}"
            )


if __name__ == "__main__":
    asyncio.run(main())
