import asyncio
from app.config.database import engine
from sqlalchemy import text

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("DESCRIBE sj_banners"))
        for r in res:
            print(r)

asyncio.run(main())
