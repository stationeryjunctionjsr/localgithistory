import asyncio, aiomysql
async def test():
    conn = await aiomysql.connect(host='127.0.0.1', port=13306, user='stationeryjunction.jsr@gmail.com', password='Jaimatadi$1607', db='sjqadb')
    async with conn.cursor() as cur:
        await cur.execute('SELECT COUNT(*) FROM sj_bundles')
        print("Bundles count:", await cur.fetchone())
    await conn.ensure_closed()
asyncio.run(test())
