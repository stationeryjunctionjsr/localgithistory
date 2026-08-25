import asyncio

import aiomysql

DB_URLS = {
    "sjqadb": {
        "host": "127.0.0.1",
        "port": 13306,
        "user": "stationeryjunction.jsr@gmail.com",
        "password": "Jaimatadi$1607",
        "db": "sjqadb",
    },
    "sjuatdb": {
        "host": "127.0.0.1",
        "port": 13306,
        "user": "stationeryjunction.jsr@gmail.com",
        "password": "Jaimatadi$1607",
        "db": "sjuatdb",
    },
}


async def run_db():
    for db_name, config in DB_URLS.items():
        try:
            conn = await aiomysql.connect(**config)
            async with conn.cursor() as cur:
                print(f"[{db_name}] Connected.")

                try:
                    await cur.execute("ALTER TABLE sj_banners DROP COLUMN user_segments;")
                except Exception as e:
                    print(e)
                try:
                    await cur.execute("ALTER TABLE sj_banners DROP COLUMN visibility_rules;")
                except Exception as e:
                    print(e)

                try:
                    await cur.execute("ALTER TABLE sj_categories DROP COLUMN images;")
                except Exception as e:
                    print(e)
                try:
                    await cur.execute("ALTER TABLE sj_categories DROP COLUMN sub_categories;")
                except Exception as e:
                    print(e)
                try:
                    await cur.execute("ALTER TABLE sj_categories DROP COLUMN category_tags;")
                except Exception as e:
                    print(e)

                try:
                    await cur.execute("ALTER TABLE sj_return_requests DROP COLUMN items;")
                except Exception as e:
                    print(e)

            await conn.commit()
            conn.close()
            print(f"[{db_name}] Done.")
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run_db())
