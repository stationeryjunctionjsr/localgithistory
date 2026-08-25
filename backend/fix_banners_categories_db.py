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

                # Banner child tables
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_banner_user_segments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    banner_id INT NOT NULL,
                    segment VARCHAR(128) NOT NULL,
                    CONSTRAINT fk_banner_user_seg FOREIGN KEY (banner_id) REFERENCES sj_banners(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_banner_visibility_rules (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    banner_id INT NOT NULL,
                    rule VARCHAR(128) NOT NULL,
                    CONSTRAINT fk_banner_vis_rule FOREIGN KEY (banner_id) REFERENCES sj_banners(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                # Category child tables
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_category_images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_id INT NOT NULL,
                    image_url VARCHAR(1024) NOT NULL,
                    CONSTRAINT fk_cat_img FOREIGN KEY (category_id) REFERENCES sj_categories(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_category_sub_categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_id INT NOT NULL,
                    sub_category VARCHAR(128) NOT NULL,
                    CONSTRAINT fk_cat_sub_cat FOREIGN KEY (category_id) REFERENCES sj_categories(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_category_category_tags (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_id INT NOT NULL,
                    tag VARCHAR(128) NOT NULL,
                    CONSTRAINT fk_cat_tag FOREIGN KEY (category_id) REFERENCES sj_categories(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

            await conn.commit()
            conn.close()
            print(f"[{db_name}] Done.")
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run_db())
