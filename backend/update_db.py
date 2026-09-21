import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

async def alter_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("No URL")
        return
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        print("Altering sj_product_reviews...")
        try:
            await conn.execute(text("ALTER TABLE sj_product_reviews ADD COLUMN user_name VARCHAR(128) DEFAULT NULL;"))
            await conn.execute(text("ALTER TABLE sj_product_reviews ADD COLUMN classification VARCHAR(64) DEFAULT NULL;"))
            print("Done.")
        except Exception as e:
            print("Error:", e)

asyncio.run(alter_db())
