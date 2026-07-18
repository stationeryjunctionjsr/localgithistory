import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path and load env
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from app.repositories.coupon_repository import coupon_repository
from app.models.schemas import CouponResponse

async def test_serialization():
    try:
        coupons = await coupon_repository.findAll()
        print(f"Retrieved {len(coupons)} coupons from DB.")
        for coupon in coupons:
            print(f"\nEvaluating coupon ID {coupon.get('_id')} (Code: {coupon.get('code')}):")
            print("Raw dict:", {k: v for k, v in coupon.items() if k != 'payload'})
            
            # Serialize to CouponResponse
            response_model = CouponResponse(**coupon)
            dumped = response_model.model_dump(by_alias=True)
            print("Successfully serialized! usedCount =", dumped.get("usedCount"))
            print("createdAt:", dumped.get("createdAt"), "updatedAt:", dumped.get("updatedAt"))
            
        print("\nAll coupons serialized successfully!")
    except Exception as e:
        print("Serialization failed with error:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_serialization())
