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
    coupons = await coupon_repository.findAll()
    print(f"Total coupons in DB: {len(coupons)}")
    for c in coupons:
        print(f"ID: {c.get('_id')}, Code: {c.get('code')}, displayId: {c.get('displayId')}")


if __name__ == "__main__":
    asyncio.run(check_db())
