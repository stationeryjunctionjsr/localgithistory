import asyncio

import aiomysql


async def run():
    try:
        conn = await aiomysql.connect(host="127.0.0.1", port=3306, user="root", password="password", db="stationery")
        async with conn.cursor() as cur:
            await cur.execute("SHOW TABLES")
            tables = await cur.fetchall()
            print(f"Connected to DB, found {len(tables)} tables.")
        conn.close()
    except Exception as e:
        print(f"Failed to connect to db: {e}")


asyncio.run(run())
