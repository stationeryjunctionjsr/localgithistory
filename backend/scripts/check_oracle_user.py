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


async def check_user():
    factory = get_async_session_factory()
    async with factory() as session:
        result = await session.execute(text("SELECT user FROM dual"))
        user = result.scalar()
        print(f"I am user: {user}")

        result = await session.execute(text("SELECT COUNT(*) FROM user_tables"))
        count = result.scalar()
        print(f"I own {count} tables.")


if __name__ == "__main__":
    asyncio.run(check_user())
