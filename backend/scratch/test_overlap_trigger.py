import sys
import os
from pathlib import Path

# Add backend to path and load env
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

import asyncio
from app.repositories.coupon_repository import coupon_repository, OverlapConflictError

async def test_overlap():
    # 1. Create first coupon for Category "Art Supplies" (ID 17)
    c1_data = {
        "typeOfDiscount": "product_discount",
        "method": "automatic",
        "discountType": "percentage",
        "discountValue": 10.0,
        "isActive": True,
        "validFrom": "2026-01-01T00:00:00",
        "validUntil": "2026-12-31T23:59:59",
        "applicableRoles": ["customer"],
        "appliesToType": "categories",
        "appliesToValueIds": ["17"],
        "force": True
    }
    
    # 2. Create second coupon for same category without force
    c2_data = {
        "typeOfDiscount": "product_discount",
        "method": "automatic",
        "discountType": "percentage",
        "discountValue": 15.0,
        "isActive": True,
        "validFrom": "2026-01-01T00:00:00",
        "validUntil": "2026-12-31T23:59:59",
        "applicableRoles": ["customer"],
        "appliesToType": "categories",
        "appliesToValueIds": ["17"],
        "force": False
    }

    # Pre-cleanup
    all_coupons = await coupon_repository.storage.findAll({})
    for c in all_coupons:
        await coupon_repository.delete(c["_id"])
        
    created1 = await coupon_repository.create(c1_data)
    print("Created first coupon:", created1)
    
    try:
        created2 = await coupon_repository.create(c2_data)
        print("Created second coupon without conflict:", created2)
    except OverlapConflictError as e:
        print("Caught OverlapConflictError successfully!")
        print("Overlap Data:", e.overlap_data)
    except Exception as e:
        print("Caught general exception:", type(e), e)
        
    # Cleanup
    for c in await coupon_repository.storage.findAll({}):
        await coupon_repository.delete(c["_id"])

if __name__ == "__main__":
    asyncio.run(test_overlap())
