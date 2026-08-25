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

                # 1. sj_referral_settings
                try:
                    await cur.execute("ALTER TABLE sj_referral_settings DROP COLUMN doc;")
                except:
                    pass
                try:
                    await cur.execute("""
                    ALTER TABLE sj_referral_settings
                    ADD COLUMN segment VARCHAR(64),
                    ADD COLUMN discount_type VARCHAR(64),
                    ADD COLUMN discount_value DECIMAL(18,2),
                    ADD COLUMN is_active TINYINT(1) DEFAULT 0;
                    """)
                except Exception as e:
                    print(e)

                # 2. sj_wishlists
                try:
                    await cur.execute("ALTER TABLE sj_wishlists DROP COLUMN items;")
                except:
                    pass
                try:
                    await cur.execute("""
                    CREATE TABLE IF NOT EXISTS sj_wishlist_items (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        wishlist_id INT NOT NULL,
                        product_id VARCHAR(64),
                        CONSTRAINT fk_sj_wishlist_item FOREIGN KEY (wishlist_id) REFERENCES sj_wishlists(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """)
                except Exception as e:
                    print(e)

                # 3. sj_sessions
                try:
                    await cur.execute("ALTER TABLE sj_sessions DROP COLUMN device;")
                except:
                    pass
                try:
                    await cur.execute("""
                    CREATE TABLE IF NOT EXISTS sj_session_devices (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        session_id INT NOT NULL,
                        device_key VARCHAR(128),
                        device_value VARCHAR(512),
                        CONSTRAINT fk_sj_session_dev FOREIGN KEY (session_id) REFERENCES sj_sessions(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """)
                except Exception as e:
                    print(e)

                # 4. sj_product_sellers
                try:
                    await cur.execute("ALTER TABLE sj_product_sellers DROP COLUMN variant_ids;")
                except:
                    pass
                try:
                    await cur.execute("""
                    CREATE TABLE IF NOT EXISTS sj_product_seller_variants (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_seller_id INT NOT NULL,
                        variant_id VARCHAR(64),
                        CONSTRAINT fk_sj_prod_sel_var FOREIGN KEY (product_seller_id) REFERENCES sj_product_sellers(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                    """)
                except Exception as e:
                    print(e)

                # 5. sj_device_subscriptions
                try:
                    await cur.execute("ALTER TABLE sj_device_subscriptions DROP COLUMN `keys`;")
                except:
                    pass
                try:
                    await cur.execute("ALTER TABLE sj_device_subscriptions DROP COLUMN subscription;")
                except:
                    pass

            await conn.commit()
            conn.close()
            print(f"[{db_name}] Done.")
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run_db())
