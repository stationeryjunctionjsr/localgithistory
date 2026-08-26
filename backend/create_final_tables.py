import asyncio
import aiomysql

async def run():
    c = await aiomysql.connect(host='127.0.0.1', port=13306, user='stationeryjunction.jsr@gmail.com', password='Jaimatadi$1607', db='sjuatdb')
    cur = await c.cursor()
    
    # 1. Create sj_ads table
    await cur.execute("""
    CREATE TABLE IF NOT EXISTS sj_ads (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        external_id VARCHAR(32) NOT NULL UNIQUE,
        name VARCHAR(255) NOT NULL,
        platform VARCHAR(64) DEFAULT 'google',
        objective VARCHAR(128) DEFAULT NULL,
        status VARCHAR(64) DEFAULT 'draft',
        budget_daily DECIMAL(10,2) DEFAULT 0,
        budget_total DECIMAL(10,2) DEFAULT 0,
        currency VARCHAR(10) DEFAULT 'INR',
        start_date DATETIME DEFAULT NULL,
        end_date DATETIME DEFAULT NULL,
        target_url VARCHAR(1024) DEFAULT NULL,
        headline VARCHAR(512) DEFAULT NULL,
        description TEXT DEFAULT NULL,
        image_url VARCHAR(1024) DEFAULT NULL,
        google_campaign_id VARCHAR(128) DEFAULT NULL,
        google_ad_group_id VARCHAR(128) DEFAULT NULL,
        meta_campaign_id VARCHAR(128) DEFAULT NULL,
        meta_ad_set_id VARCHAR(128) DEFAULT NULL,
        utm_source VARCHAR(128) DEFAULT NULL,
        utm_medium VARCHAR(128) DEFAULT NULL,
        utm_campaign VARCHAR(128) DEFAULT NULL,
        google_conversion_id VARCHAR(128) DEFAULT NULL,
        google_conversion_label VARCHAR(128) DEFAULT NULL,
        meta_pixel_id VARCHAR(128) DEFAULT NULL,
        notes TEXT DEFAULT NULL,
        impressions INT DEFAULT 0,
        clicks INT DEFAULT 0,
        leads INT DEFAULT 0,
        purchases INT DEFAULT 0,
        add_to_cart INT DEFAULT 0,
        conversions INT DEFAULT 0,
        conversion_value DECIMAL(12,2) DEFAULT 0,
        ctr DECIMAL(10,4) DEFAULT 0,
        cvr DECIMAL(10,4) DEFAULT 0,
        created_at DATETIME DEFAULT NULL,
        updated_at DATETIME DEFAULT NULL,
        launched_at DATETIME DEFAULT NULL
    ) ENGINE=InnoDB;
    """)

    # 2. Create sj_seller_payouts table
    await cur.execute("""
    CREATE TABLE IF NOT EXISTS sj_seller_payouts (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        external_id VARCHAR(32) NOT NULL UNIQUE,
        seller_id VARCHAR(64) NOT NULL,
        amount DECIMAL(12,2) NOT NULL,
        period_start DATETIME DEFAULT NULL,
        period_end DATETIME DEFAULT NULL,
        notes TEXT DEFAULT NULL,
        created_at DATETIME DEFAULT NULL,
        updated_at DATETIME DEFAULT NULL
    ) ENGINE=InnoDB;
    """)

    # 3. Create sj_seller_payout_sub_orders table for the subOrderIds array
    await cur.execute("""
    CREATE TABLE IF NOT EXISTS sj_seller_payout_sub_orders (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        payout_id INT NOT NULL,
        sub_order_id VARCHAR(64) NOT NULL,
        FOREIGN KEY (payout_id) REFERENCES sj_seller_payouts(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;
    """)

    await c.commit()
    print("Tables created.")

asyncio.run(run())
