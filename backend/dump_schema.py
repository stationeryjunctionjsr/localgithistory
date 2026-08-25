import asyncio

import aiomysql


async def dump_schema():
    config = {
        "host": "127.0.0.1",
        "port": 13306,
        "user": "stationeryjunction.jsr@gmail.com",
        "password": "Jaimatadi$1607",
        "db": "sjuatdb",
    }
    try:
        conn = await aiomysql.connect(**config)
        async with conn.cursor() as cur:
            await cur.execute("SHOW TABLES")
            tables = [r[0] for r in await cur.fetchall()]

            with open("backend/scripts/schema_mysql.sql", "w") as f:
                f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
                f.write("SET NAMES utf8mb4;\n\n")

                for table in tables:
                    await cur.execute(f"SHOW CREATE TABLE `{table}`")
                    res = await cur.fetchone()
                    create_sql = res[1]
                    f.write(create_sql + ";\n\n")

                f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
        conn.close()
        print("Schema successfully dumped.")
    except Exception as e:
        print(f"Error: {e}")


asyncio.run(dump_schema())
