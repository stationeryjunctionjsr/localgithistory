import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

async def alter_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        return
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        print("Altering sj_orders...")
        queries = [
            "ALTER TABLE sj_orders ADD COLUMN ship_address VARCHAR(255) DEFAULT NULL;",
            "ALTER TABLE sj_orders ADD COLUMN ship_district VARCHAR(100) DEFAULT NULL;",
            "ALTER TABLE sj_orders ADD COLUMN ship_country VARCHAR(100) DEFAULT 'India';",
            "ALTER TABLE sj_orders ADD COLUMN ship_google_location VARCHAR(255) DEFAULT NULL;",
            "ALTER TABLE sj_orders ADD COLUMN ship_latitude DOUBLE DEFAULT NULL;",
            "ALTER TABLE sj_orders ADD COLUMN ship_longitude DOUBLE DEFAULT NULL;",
            
            "ALTER TABLE sj_orders ADD COLUMN bill_address VARCHAR(255) DEFAULT NULL;",
            "ALTER TABLE sj_orders ADD COLUMN bill_district VARCHAR(100) DEFAULT NULL;",
            "ALTER TABLE sj_orders ADD COLUMN bill_country VARCHAR(100) DEFAULT 'India';",
            "ALTER TABLE sj_orders ADD COLUMN bill_google_location VARCHAR(255) DEFAULT NULL;",
            "ALTER TABLE sj_orders ADD COLUMN bill_latitude DOUBLE DEFAULT NULL;",
            "ALTER TABLE sj_orders ADD COLUMN bill_longitude DOUBLE DEFAULT NULL;",
        ]
        for q in queries:
            try:
                await conn.execute(text(q))
            except Exception as e:
                print("Skipping (might exist):", e)
        print("Done.")

asyncio.run(alter_db())
