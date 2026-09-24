import asyncio
from app.db.storage_factory import get_storage
import ast

async def test_zones():
    zones = await get_storage('deliveryZones').findAll()
    for z in zones:
        val = z.pincodes
        if isinstance(val, list):
            z_pincodes = [str(p) for p in val]
        elif isinstance(val, str) and val.startswith('['):
            try:
                z_pincodes = ast.literal_eval(val)
            except:
                z_pincodes = [p.strip() for p in val.split(',')]
        else:
            z_pincodes = [p.strip() for p in (val or "").split(',')]
        
        if '123456' in z_pincodes:
            print(f"MATCH! Zone {z.id}: {z_pincodes}")

asyncio.run(test_zones())
