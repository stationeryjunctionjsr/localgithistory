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

                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_user_addresses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    is_primary TINYINT(1) DEFAULT 0,
                    street VARCHAR(255),
                    city VARCHAR(100),
                    state VARCHAR(100),
                    pincode VARCHAR(20),
                    phone VARCHAR(20),
                    CONSTRAINT fk_usr_addr FOREIGN KEY (user_id) REFERENCES sj_users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_seller_pincodes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    pincode VARCHAR(20) NOT NULL,
                    pincode_type ENUM('serviceable', 'urgent', 'slot') NOT NULL,
                    CONSTRAINT fk_usr_pin FOREIGN KEY (user_id) REFERENCES sj_users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_seller_zones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    zone_name VARCHAR(255) NOT NULL,
                    CONSTRAINT fk_usr_zone FOREIGN KEY (user_id) REFERENCES sj_users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                try:
                    await cur.execute("""
                    ALTER TABLE sj_users 
                    ADD COLUMN allow_delivery_slots TINYINT(1) DEFAULT 0,
                    ADD COLUMN allow_urgent_delivery TINYINT(1) DEFAULT 0,
                    DROP COLUMN address, 
                    DROP COLUMN saved_addresses, 
                    DROP COLUMN seller_permissions, 
                    DROP COLUMN service_area_zones;
                    """)
                    print(f"[{db_name}] Altered sj_users.")
                except Exception as e:
                    print(f"[{db_name}] sj_users alter skipped: {e}")

            await conn.commit()
            conn.close()
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run())
