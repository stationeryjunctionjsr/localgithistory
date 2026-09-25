import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('mysql+aiomysql://stationeryjunction.jsr%40gmail.com:Jaimatadi%241607@127.0.0.1:13306/sjqadb')
    async with engine.connect() as conn:
        res = await conn.execute(text("SHOW FULL PROCESSLIST"))
        for row in res.fetchall():
            print(row)
            if row[4] == 'Sleep' and row[5] > 30: # Sleep over 30 seconds
                print(f"Killing process {row[0]}")
                try:
                    await conn.execute(text(f"KILL {row[0]}"))
                    print(f"Killed {row[0]}")
                except Exception as e:
                    print(f"Could not kill {row[0]}: {e}")
        await conn.commit()

asyncio.run(main())
