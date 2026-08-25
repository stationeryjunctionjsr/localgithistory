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

                # sj_saved_for_later
                try:
                    await cur.execute("ALTER TABLE sj_saved_for_later DROP COLUMN doc;")
                except:
                    pass
                try:
                    await cur.execute("""
                    ALTER TABLE sj_saved_for_later 
                    ADD COLUMN user_id VARCHAR(64),
                    ADD COLUMN product_id VARCHAR(64),
                    ADD COLUMN saved_at DATETIME;
                    """)
                except Exception as e:
                    print(f"sj_saved_for_later: {e}")

                # sj_tracking
                try:
                    await cur.execute("ALTER TABLE sj_tracking DROP COLUMN doc;")
                except:
                    pass
                try:
                    await cur.execute("""
                    ALTER TABLE sj_tracking 
                    ADD COLUMN event_type VARCHAR(128),
                    ADD COLUMN user_id VARCHAR(64),
                    ADD COLUMN session_id VARCHAR(64),
                    ADD COLUMN event_timestamp DATETIME,
                    ADD COLUMN search_term VARCHAR(255),
                    ADD COLUMN results_count INT,
                    ADD COLUMN product_id VARCHAR(64),
                    ADD COLUMN product_name VARCHAR(255),
                    ADD COLUMN segment VARCHAR(64),
                    ADD COLUMN page VARCHAR(255),
                    ADD COLUMN reason VARCHAR(255),
                    ADD COLUMN filter_type VARCHAR(64),
                    ADD COLUMN filter_value VARCHAR(255),
                    ADD COLUMN cart_value DECIMAL(18,2),
                    ADD COLUMN os VARCHAR(64),
                    ADD COLUMN browser VARCHAR(64),
                    ADD COLUMN ip_address VARCHAR(64);
                    """)
                except Exception as e:
                    print(f"sj_tracking: {e}")

                try:
                    await cur.execute("""
                    CREATE TABLE IF NOT EXISTS sj_tracking_products (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        tracking_id INT NOT NULL,
                        product_id VARCHAR(64),
                        CONSTRAINT fk_sj_tracking_prod FOREIGN KEY (tracking_id) REFERENCES sj_tracking(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """)
                except Exception as e:
                    print(e)
                try:
                    await cur.execute("""
                    CREATE TABLE IF NOT EXISTS sj_tracking_payload (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        tracking_id INT NOT NULL,
                        payload_key VARCHAR(128),
                        payload_value TEXT,
                        CONSTRAINT fk_sj_tracking_pay FOREIGN KEY (tracking_id) REFERENCES sj_tracking(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """)
                except Exception as e:
                    print(e)

            await conn.commit()
            conn.close()
            print(f"[{db_name}] Done.")
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run_db())
