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
        result = await session.execute(text("SELECT sequence_name FROM user_sequences"))
        rows = result.fetchall()
        print(f"Sequences found: {len(rows)}")
        for row in rows:
            print(f"  Sequence: {row.sequence_name}")


if __name__ == "__main__":
    asyncio.run(main())
