import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def main():
    try:
        f = get_async_session_factory()
        async with f() as s:
            res = await s.execute(text("SHOW TABLES"))
            tables = [r[0] for r in res.fetchall()]
            print("Successfully connected to DB!")
            print(f"Found {len(tables)} tables.")
    except Exception as e:
        print(f"Error connecting to DB: {e}")

asyncio.run(main())
