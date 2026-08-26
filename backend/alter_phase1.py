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

                # Products
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_product_images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    image_url VARCHAR(1024) NOT NULL,
                    order_index INT DEFAULT 0,
                    CONSTRAINT fk_prod_img FOREIGN KEY (product_id) REFERENCES sj_products(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_product_videos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    video_url VARCHAR(1024) NOT NULL,
                    order_index INT DEFAULT 0,
                    CONSTRAINT fk_prod_vid FOREIGN KEY (product_id) REFERENCES sj_products(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_product_tags (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    tag VARCHAR(255) NOT NULL,
                    CONSTRAINT fk_prod_tag FOREIGN KEY (product_id) REFERENCES sj_products(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_product_attributes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    attr_name VARCHAR(255) NOT NULL,
                    CONSTRAINT fk_prod_attr FOREIGN KEY (product_id) REFERENCES sj_products(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_product_variant_combinations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    sku VARCHAR(255),
                    price DECIMAL(10,2),
                    stock INT DEFAULT 0,
                    CONSTRAINT fk_prod_var FOREIGN KEY (product_id) REFERENCES sj_products(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_product_variant_options (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    combination_id INT NOT NULL,
                    attr_name VARCHAR(255) NOT NULL,
                    attr_value VARCHAR(255) NOT NULL,
                    CONSTRAINT fk_prod_var_opt FOREIGN KEY (combination_id) REFERENCES sj_product_variant_combinations(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_product_details (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    detail_key VARCHAR(255) NOT NULL,
                    detail_value TEXT,
                    CONSTRAINT fk_prod_det FOREIGN KEY (product_id) REFERENCES sj_products(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                try:
                    await cur.execute(
                        "ALTER TABLE sj_products DROP COLUMN images, DROP COLUMN videos, DROP COLUMN tags, DROP COLUMN variant_attributes, DROP COLUMN variant_combinations, DROP COLUMN details;"
                    )
                    print(f"[{db_name}] Dropped JSON columns from sj_products.")
                except Exception as e:
                    print(f"[{db_name}] sj_products alter skipped: {e}")

                # Orders
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_order_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id VARCHAR(64) NOT NULL,
                    product_id VARCHAR(64) NOT NULL,
                    quantity INT NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    product_name VARCHAR(255),
                    sell_as_case TINYINT(1) DEFAULT 0,
                    CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES sj_orders(external_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                try:
                    await cur.execute("""
                    ALTER TABLE sj_orders 
                    DROP COLUMN items, DROP COLUMN shipping_address, DROP COLUMN billing_address,
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
                    print(f"[{db_name}] Altered sj_orders.")
                except Exception as e:
                    print(f"[{db_name}] sj_orders alter skipped: {e}")

                # Sub Orders
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_sub_order_variants (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sub_order_id VARCHAR(64) NOT NULL,
                    variant_id VARCHAR(64) NOT NULL,
                    CONSTRAINT fk_sub_ord_var FOREIGN KEY (sub_order_id) REFERENCES sj_sub_orders(external_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                try:
                    await cur.execute("ALTER TABLE sj_sub_orders DROP COLUMN variant_ids;")
                    print(f"[{db_name}] Dropped variant_ids from sj_sub_orders.")
                except Exception as e:
                    print(f"[{db_name}] sj_sub_orders alter skipped: {e}")

                # Carts
                await cur.execute("""
                CREATE TABLE IF NOT EXISTS sj_cart_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    cart_id VARCHAR(64) NOT NULL,
                    product_id VARCHAR(64) NOT NULL,
                    quantity INT NOT NULL,
                    sell_as_case TINYINT(1) DEFAULT 0,
                    CONSTRAINT fk_cart_item_cart FOREIGN KEY (cart_id) REFERENCES sj_carts(external_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)

                try:
                    await cur.execute("ALTER TABLE sj_carts DROP COLUMN items;")
                    print(f"[{db_name}] Dropped items from sj_carts.")
                except Exception as e:
                    print(f"[{db_name}] sj_carts alter skipped: {e}")

            await conn.commit()
            conn.close()
        except Exception as e:
            print(f"[{db_name}] Error: {e}")


asyncio.run(run())
