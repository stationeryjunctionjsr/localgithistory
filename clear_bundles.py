import asyncio
import os
import aiomysql

async def test():
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "13306"))
    user = os.environ.get("DB_USER", "")
    password = os.environ.get("DB_PASSWORD", "")
    db = os.environ.get("DB_NAME", "sjqadb")
    conn = await aiomysql.connect(host=host, port=port, user=user, password=password, db=db)
    async with conn.cursor() as cur:
        await cur.execute("DELETE FROM sj_bundles WHERE name LIKE '%Test%' OR name LIKE '%Volume Bundle%'")
        await conn.commit()
    await conn.ensure_closed()

asyncio.run(test())
