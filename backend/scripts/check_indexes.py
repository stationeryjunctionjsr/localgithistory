import asyncio
from dotenv import load_dotenv

load_dotenv()
from sqlalchemy import text
from app.config.database import get_async_engine


async def check_indexes():
    engine = get_async_engine()
    if not engine:
        print("Oracle not configured.")
        return

    query = """
    SELECT index_name, column_name 
    FROM all_ind_columns 
    WHERE table_name = 'SJ_PRODUCTS'
    ORDER BY index_name, column_position
    """

    async with engine.connect() as conn:
        result = await conn.execute(text(query))
        rows = result.fetchall()
        print("Current Indexes on SJ_PRODUCTS:")
        for row in rows:
            print(f"Index: {row[0]}, Column: {row[1]}")


if __name__ == "__main__":
    asyncio.run(check_indexes())
