import asyncio
import os
import sys
from pathlib import Path

# Add backend root so app imports work
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory

async def main():
    print("Connecting to database...")
    factory = get_async_session_factory()
    if not factory:
        print("No factory created. Check DATABASE_URL.")
        return
    async with factory() as session:
        print("Querying table sj_feature_flags...")
        try:
            result = await session.execute(text("SELECT * FROM sj_feature_flags"))
            rows = result.fetchall()
            print(f"Found {len(rows)} feature flags:")
            for r in rows:
                print(r)
        except Exception as e:
            print(f"Error querying: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
