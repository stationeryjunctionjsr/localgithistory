import sys
import os
from pathlib import Path

# Add backend to path and load env
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

import asyncio
from app.repositories.coupon_repository import coupon_repository
from app.models.schemas import CouponResponse


async def test_direct():
    # 1. Create a coupon first
    coupon_data = {
        "typeOfDiscount": "product_discount",
        "method": "discount_code",
        "code": "TESTID10",
        "discountType": "percentage",
        "discountValue": 10.0,
        "isActive": True,
        "validFrom": "2026-01-01T00:00:00",
        "validUntil": "2026-12-31T23:59:59",
        "applicableRoles": ["customer"],
        "appliesToType": "all",
        "force": True,
    }

    # Pre-cleanup
    existing = await coupon_repository.findByCode("TESTID10")
    if existing:
        await coupon_repository.delete(existing["_id"])

    created = await coupon_repository.create(coupon_data)
    print("Created coupon:", created)

    # Check repository findOne
    retrieved = await coupon_repository.findByCode("TESTID10")
    print("Retrieved coupon:", retrieved)

    # Validate the Pydantic serialization
    response_model = CouponResponse(**retrieved)
    print("CouponResponse dict():", response_model.dict())
    print("CouponResponse dict(by_alias=True):", response_model.dict(by_alias=True))

    # Cleanup
    await coupon_repository.delete(created["_id"])


if __name__ == "__main__":
    asyncio.run(test_direct())
