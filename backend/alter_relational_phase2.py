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
                # FAQs child table
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_faq_items (
                  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                  section_id VARCHAR(64) NOT NULL,
                  question TEXT NOT NULL,
                  answer TEXT NOT NULL,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  CONSTRAINT fk_faq_section_id FOREIGN KEY (section_id) REFERENCES sj_faq_sections(external_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                print(f"[{db_name}] Created sj_faq_items.")

                try:
                    await cur.execute("ALTER TABLE sj_faq_sections DROP COLUMN faqs;")
                    await cur.execute(
                        "ALTER TABLE sj_faq_sections ADD COLUMN icon VARCHAR(255) DEFAULT 'help-circle-outline';"
                    )
                    print(f"[{db_name}] Dropped faqs, added icon to sj_faq_sections.")
                except Exception as e:
                    print(f"[{db_name}] Error altering sj_faq_sections: {e}")

                # Customer segments columns
                try:
                    await cur.execute("ALTER TABLE sj_customer_segments DROP COLUMN criteria;")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN min_avg_order_value DECIMAL(10,2);")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN max_avg_order_value DECIMAL(10,2);")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN start_date DATETIME;")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN end_date DATETIME;")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN min_order_freq INT;")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN max_order_freq INT;")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN state VARCHAR(255);")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN district VARCHAR(255);")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN app_user TINYINT(1);")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN behavior VARCHAR(255);")
                    await cur.execute("ALTER TABLE sj_customer_segments ADD COLUMN role VARCHAR(64);")
                    print(f"[{db_name}] Altered sj_customer_segments.")
                except Exception as e:
                    print(f"[{db_name}] Error altering sj_customer_segments: {e}")

            await conn.commit()
            conn.close()
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run())
