import asyncio

import aiomysql


async def run():
    config = {
        "host": "127.0.0.1",
        "port": 13306,
        "user": "stationeryjunction.jsr@gmail.com",
        "password": "Jaimatadi$1607",
        "db": "sjuatdb",
    }
    c = await aiomysql.connect(**config)
    cur = await c.cursor()
    print("--- sj_payments ---")
    await cur.execute("DESCRIBE sj_payments;")
    for row in await cur.fetchall():
        print(row)
    print("--- sj_coupons ---")
    await cur.execute("DESCRIBE sj_coupons;")
    for row in await cur.fetchall():
        print(row)
    print("--- sj_tracking ---")
    await cur.execute("DESCRIBE sj_tracking;")
    for row in await cur.fetchall():
        print(row)


asyncio.run(run())
