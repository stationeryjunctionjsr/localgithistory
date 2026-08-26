import asyncio

import aiomysql

urls = {
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


async def run():
    for db_name, config in urls.items():
        try:
            conn = await aiomysql.connect(**config)
            async with conn.cursor() as cur:
                print(f"[{db_name}] Connected.")
                try:
                    await cur.execute("""
                    ALTER TABLE sj_orders 
                    DROP COLUMN shipping_address, 
                    DROP COLUMN billing_address,
                    ADD COLUMN ship_name VARCHAR(255),
                    ADD COLUMN ship_street VARCHAR(255),
                    ADD COLUMN ship_city VARCHAR(255),
                    ADD COLUMN ship_state VARCHAR(255),
                    ADD COLUMN ship_pincode VARCHAR(20),
                    ADD COLUMN ship_phone VARCHAR(20),
                    ADD COLUMN bill_name VARCHAR(255),
                    ADD COLUMN bill_street VARCHAR(255),
                    ADD COLUMN bill_city VARCHAR(255),
                    ADD COLUMN bill_state VARCHAR(255),
                    ADD COLUMN bill_pincode VARCHAR(20),
                    ADD COLUMN bill_phone VARCHAR(20);
                    """)
                    print(f"[{db_name}] Fixed addresses in sj_orders.")
                except Exception as e:
                    print(f"[{db_name}] sj_orders alter skipped: {e}")
            await conn.commit()
            conn.close()
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run())
