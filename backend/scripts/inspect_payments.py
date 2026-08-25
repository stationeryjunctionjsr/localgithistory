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
        print("DATABASE_URL not set")
        return

    try:
        async with factory() as session:
            print("Querying SELECT COUNT(*) FROM sj_payments...")
            r = await session.execute(text("SELECT COUNT(*) FROM sj_payments"))
            count = r.scalar()
            print(f"Total payments in DB: {count}")
    except Exception as e:
        print(f"Error querying sj_payments: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
