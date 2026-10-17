import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def run():
    # Connect without a specific database to list all databases
    base_url = os.environ["DATABASE_URL"]
    url = base_url.rsplit("/", 1)[0] + "/"
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        res = await conn.execute(text("SHOW DATABASES;"))
        print([row[0] for row in res.fetchall()])
    await engine.dispose()

asyncio.run(run())
