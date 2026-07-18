import asyncio
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from app.config.database import get_async_engine

async def add_indexes():
    engine = get_async_engine()
    if not engine:
        print("Oracle not configured.")
        return

    statements = [
        "CREATE INDEX ix_sj_products_brand ON sj_products (brand)",
        "CREATE INDEX ix_sj_products_subcat ON sj_products (sub_category)",
        "CREATE INDEX ix_sj_products_name_lower ON sj_products (LOWER(name))",
    ]

    async with engine.begin() as conn:
        for stmt in statements:
            try:
                print(f"Executing: {stmt}")
                await conn.execute(text(stmt))
                print("Success.")
            except Exception as e:
                if "already exists" in str(e).lower() or "ORA-00955" in str(e):
                    print("Index already exists.")
                else:
                    print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(add_indexes())
