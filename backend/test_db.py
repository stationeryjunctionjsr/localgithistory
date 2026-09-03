import asyncio
from app.config.database import get_async_engine
from sqlalchemy import text
async def main():
    engine = get_async_engine()
    async with engine.begin() as conn:
        res = await conn.execute(text('SHOW COLUMNS FROM sj_banners'))
        for r in res:
            print(r)
if __name__ == '__main__':
    asyncio.run(main())