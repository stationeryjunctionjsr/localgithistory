import asyncio
import os
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_root))

from app.db.storage_factory import get_storage
from sqlalchemy import text

async def test():
    storage = get_storage("deliverySlots")
    factory = storage._factory()
    table = storage.table_name
    print(f"Table name is {table}")
    async with factory() as session:
        for col_name in ['date', '"date"', '"DATE"', 'date_val']:
            try:
                res = await session.execute(text(f"SELECT {col_name} FROM {table} WHERE ROWNUM = 1"))
                print(f"Success with {col_name}")
            except Exception as e:
                print(f"Failed with {col_name}: {e}")

if __name__ == "__main__":
    asyncio.run(test())
