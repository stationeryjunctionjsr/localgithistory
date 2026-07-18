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


async def check_users():
    factory = get_async_session_factory()
    async with factory() as session:
        result = await session.execute(text("SELECT email, role FROM sj_users"))
        users = result.all()
        print("Users in sj_users:")
        for user in users:
            print(f"- {user.email} ({user.role})")


if __name__ == "__main__":
    asyncio.run(check_users())
