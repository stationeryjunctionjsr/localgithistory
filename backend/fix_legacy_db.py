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

                # 1. sj_payments
                try:
                    await cur.execute("ALTER TABLE sj_payments DROP COLUMN doc;")
                except:
                    pass
                await cur.execute("""
                ALTER TABLE sj_payments 
                ADD COLUMN order_id VARCHAR(64),
                ADD COLUMN user_id VARCHAR(64),
                ADD COLUMN user_id_formatted VARCHAR(64),
                ADD COLUMN customer_name VARCHAR(255),
                ADD COLUMN order_date DATETIME,
                ADD COLUMN payment_method VARCHAR(64),
                ADD COLUMN amount_paid DECIMAL(18,2) DEFAULT 0,
                ADD COLUMN amount_remaining DECIMAL(18,2) DEFAULT 0,
                ADD COLUMN total_amount DECIMAL(18,2) DEFAULT 0,
                ADD COLUMN payment_id VARCHAR(128);
                """)
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_payment_entries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    payment_id INT NOT NULL,
                    entry_id VARCHAR(64),
                    amount DECIMAL(18,2) DEFAULT 0,
                    payment_method VARCHAR(64),
                    paid_at DATETIME,
                    image VARCHAR(1024),
                    notes TEXT,
                    verified TINYINT(1) DEFAULT 0,
                    created_at DATETIME,
                    CONSTRAINT fk_sj_payment_ent FOREIGN KEY (payment_id) REFERENCES sj_payments(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                # 2. sj_coupons
                try:
                    await cur.execute("ALTER TABLE sj_coupons DROP COLUMN doc;")
                except:
                    pass
                await cur.execute("""
                ALTER TABLE sj_coupons 
                ADD COLUMN code VARCHAR(64),
                ADD COLUMN discount_type VARCHAR(32),
                ADD COLUMN discount_value DECIMAL(18,2),
                ADD COLUMN min_order_value DECIMAL(18,2),
                ADD COLUMN max_uses INT,
                ADD COLUMN used_count INT DEFAULT 0,
                ADD COLUMN start_date DATETIME,
                ADD COLUMN end_date DATETIME,
                ADD COLUMN is_active TINYINT(1) DEFAULT 1;
                """)

                # 3. sj_saved_for_later
                try:
                    await cur.execute("ALTER TABLE sj_saved_for_later DROP COLUMN doc;")
                except:
                    pass
                await cur.execute("""
                ALTER TABLE sj_saved_for_later 
                ADD COLUMN user_id VARCHAR(64),
                ADD COLUMN product_id VARCHAR(64),
                ADD COLUMN saved_at DATETIME;
                """)

                # 4. sj_tracking
                try:
                    await cur.execute("ALTER TABLE sj_tracking DROP COLUMN doc;")
                except:
                    pass
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
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_tracking_products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tracking_id INT NOT NULL,
                    product_id VARCHAR(64),
                    CONSTRAINT fk_sj_tracking_prod FOREIGN KEY (tracking_id) REFERENCES sj_tracking(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_tracking_payload (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tracking_id INT NOT NULL,
                    payload_key VARCHAR(128),
                    payload_value TEXT,
                    CONSTRAINT fk_sj_tracking_pay FOREIGN KEY (tracking_id) REFERENCES sj_tracking(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

            await conn.commit()
            conn.close()
            print(f"[{db_name}] Done.")
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run_db())
