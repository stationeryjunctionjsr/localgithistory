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
                # Customer Segments Users child table
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_customer_segment_users (
                  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                  segment_id VARCHAR(64) NOT NULL,
                  user_id VARCHAR(64) NOT NULL,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  CONSTRAINT fk_segment_id FOREIGN KEY (segment_id) REFERENCES sj_customer_segments(external_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                print(f"[{db_name}] Created sj_customer_segment_users.")

                try:
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN is_system TINYINT(1) DEFAULT 0;")
                    print(f"[{db_name}] Added is_system to sj_customer_segments.")
                except Exception as e:
                    print(f"[{db_name}] Error altering sj_customer_segments: {e}")

            await conn.commit()
            conn.close()
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run())
