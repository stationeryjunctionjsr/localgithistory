import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def main():
    factory = get_async_session_factory()
    async with factory() as session:
        await session.execute(text("ALTER TABLE sj_products ADD COLUMN rating DECIMAL(3, 1) DEFAULT 0.0"))
        await session.execute(text("ALTER TABLE sj_products ADD COLUMN reviews INT DEFAULT 0"))
        await session.commit()
        print("Successfully added rating and reviews to sj_products in sjuatdb")

asyncio.run(main())
