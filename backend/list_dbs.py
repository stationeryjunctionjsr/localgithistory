import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def run():
    engine = create_async_engine('mysql+aiomysql://stationeryjunction.jsr%40gmail.com:Jaimatadi%241607@127.0.0.1:13306/')
    async with engine.begin() as conn:
        res = await conn.execute(text("SHOW DATABASES;"))
        print([row[0] for row in res.fetchall()])

asyncio.run(run())
