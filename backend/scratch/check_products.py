import sys
import os
from pathlib import Path

# Add backend to path and load env
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

import asyncio
from app.repositories.coupon_repository import coupon_repository


async def check_db():
    cats = await coupon_repository._category_storage.findAll()
    print("Categories in DB:")
    for c in cats:
        print(f"ID: {c.get('_id')}, Name: {c.get('name')}")


if __name__ == "__main__":
    asyncio.run(check_db())
