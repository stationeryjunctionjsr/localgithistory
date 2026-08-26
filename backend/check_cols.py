import asyncio

import aiomysql


async def run():
    conn = await aiomysql.connect(
        host="127.0.0.1", port=13306, user="stationeryjunction.jsr@gmail.com", password="Jaimatadi$1607", db="sjqadb"
    )
    cur = await conn.cursor()

    await cur.execute("SHOW TABLES")
    rows = await cur.fetchall()
    print("Tables:", [r[0] for r in rows])

    await cur.execute("DESCRIBE sj_orders")
    rows = await cur.fetchall()
    print("sj_orders:", [r[0] for r in rows])

    await cur.execute("DESCRIBE sj_sub_orders")
    rows = await cur.fetchall()
    print("sj_sub_orders:", [r[0] for r in rows])

    await cur.execute("DESCRIBE sj_carts")
    rows = await cur.fetchall()
    print("sj_carts:", [r[0] for r in rows])
    conn.close()


asyncio.run(run())
