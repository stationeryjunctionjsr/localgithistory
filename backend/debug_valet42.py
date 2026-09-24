import asyncio
from app.db.storage_factory import get_storage

async def test_zones():
    zones = await get_storage('deliveryZones').findAll()
    for z in zones:
        if '123456' in (z.pincodes or ""):
            print(f"Zone {z.id}: pincodes='{z.pincodes}'")

asyncio.run(test_zones())
