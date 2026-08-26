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

                # 1. Commission Settings
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_commission_settings_tiers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    setting_id INT NOT NULL,
                    min_val DECIMAL(10,2) DEFAULT 0,
                    max_val DECIMAL(10,2),
                    commission_pct DECIMAL(5,2) NOT NULL,
                    CONSTRAINT fk_comm_tier FOREIGN KEY (setting_id) REFERENCES sj_commission_settings(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                try:
                    await cur.execute("ALTER TABLE sj_commission_settings DROP COLUMN tiers;")
                except Exception as e:
                    pass

                # 2. Valet Availability
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_valet_availability_slots (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    availability_id INT NOT NULL,
                    slot VARCHAR(64) NOT NULL,
                    CONSTRAINT fk_valet_slot FOREIGN KEY (availability_id) REFERENCES sj_valet_availability(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_valet_availability_zones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    availability_id INT NOT NULL,
                    zone VARCHAR(255) NOT NULL,
                    CONSTRAINT fk_valet_zone FOREIGN KEY (availability_id) REFERENCES sj_valet_availability(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                try:
                    await cur.execute("ALTER TABLE sj_valet_availability DROP COLUMN slots, DROP COLUMN zones;")
                except Exception as e:
                    pass

                # 3. Seller Requests
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_seller_request_attachments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    request_id INT NOT NULL,
                    url VARCHAR(1024) NOT NULL,
                    CONSTRAINT fk_req_att FOREIGN KEY (request_id) REFERENCES sj_seller_requests(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_seller_request_responses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    request_id INT NOT NULL,
                    admin_id VARCHAR(64),
                    response_text TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_req_resp FOREIGN KEY (request_id) REFERENCES sj_seller_requests(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                try:
                    await cur.execute("ALTER TABLE sj_seller_requests DROP COLUMN attachments, DROP COLUMN responses;")
                except Exception as e:
                    pass

            await conn.commit()
            conn.close()
            print(f"[{db_name}] Done.")
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run())
