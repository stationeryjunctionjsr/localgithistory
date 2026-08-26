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
                # Add mapping table
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_bundle_products (
                  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                  bundle_id VARCHAR(64) NOT NULL,
                  product_id VARCHAR(64) NOT NULL,
                  quantity INT DEFAULT 1,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  CONSTRAINT fk_bundle_id FOREIGN KEY (bundle_id) REFERENCES sj_bundles(external_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                print(f"[{db_name}] Created sj_bundle_products.")

                # Remove JSON column
                try:
                    await cur.execute("ALTER TABLE sj_bundles DROP COLUMN products;")
                    print(f"[{db_name}] Dropped products column from sj_bundles.")
                except Exception as e:
                    print(f"[{db_name}] Drop column failed (maybe already dropped): {e}")

            await conn.commit()
            conn.close()
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run())
