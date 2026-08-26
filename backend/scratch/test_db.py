import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def main():
    try:
        url = os.environ.get("DATABASE_URL")
        print("URL:", url)
        engine = create_async_engine(url, echo=True)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 FROM DUAL"))
            print(result.scalar())
        print("done oracle")
    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
