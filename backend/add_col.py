import asyncio
from sqlalchemy import text
from app.config.database import get_async_session_factory

async def main():
    factory = get_async_session_factory()
    async with factory() as session:
        await session.execute(text("ALTER TABLE sj_banners ADD COLUMN zone_ids JSON"))
        await session.commit()
        print("Successfully added zone_ids to sj_banners in sjuatdb")

asyncio.run(main())
