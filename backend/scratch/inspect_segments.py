import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory


async def main():
    factory = get_async_session_factory()
    if not factory:
        print("Async session factory not available.")
        return

    async with factory() as session:
        result = await session.execute(text("SELECT * FROM sj_customer_segments"))
        rows = result.fetchall()
        print(f"Total rows in sj_customer_segments: {len(rows)}")
        for r in rows:
            print(dict(r._mapping))


if __name__ == "__main__":
    asyncio.run(main())
