import asyncio
import aiomysql

async def run():
    c = await aiomysql.connect(host='127.0.0.1', port=13306, user='stationeryjunction.jsr@gmail.com', password='Jaimatadi$1607', db='sjuatdb')
    cur = await c.cursor()
    
    # 1. Product variant attributes
    await cur.execute("""
    CREATE TABLE IF NOT EXISTS sj_product_variant_attributes (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        attribute_name VARCHAR(128) NOT NULL,
        FOREIGN KEY (product_id) REFERENCES sj_products(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)
    
    # 2. Product variants (the combinations)
    await cur.execute("""
    CREATE TABLE IF NOT EXISTS sj_product_variants (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        sku VARCHAR(128) DEFAULT NULL,
        price DECIMAL(18,2) DEFAULT NULL,
        price_per_case DECIMAL(18,2) DEFAULT NULL,
        stock INT DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES sj_products(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)
    
    await cur.execute("""
    CREATE TABLE IF NOT EXISTS sj_product_variant_combo_attrs (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        variant_id INT NOT NULL,
        attr_name VARCHAR(128) NOT NULL,
        attr_value VARCHAR(128) NOT NULL,
        FOREIGN KEY (variant_id) REFERENCES sj_product_variants(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)

    try:
        await cur.execute("ALTER TABLE sj_products DROP COLUMN variants;")
    except:
        pass
    try:
        await cur.execute("ALTER TABLE sj_products DROP COLUMN variant_attributes;")
    except:
        pass
    
    await c.commit()
    print("Child tables created and JSON columns dropped.")

asyncio.run(run())
