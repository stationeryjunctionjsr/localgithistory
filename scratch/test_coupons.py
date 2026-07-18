import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from app.config.settings import settings
from app.db.storage_factory import get_storage
from sqlalchemy import text
from app.config.database import get_async_session_factory, get_async_engine

async def main():
    print("[*] Starting Coupons UAT Database Verification...")

    settings.table_suffix = "_UAT"
    coupon_store = get_storage("coupons")
    
    # Clean up leftover
    existing = await coupon_store.findOne({"code": "TESTUATCOUPON"})
    if existing:
        print("  Cleaning up leftover test coupon...")
        await coupon_store.delete(existing["_id"])

    coupon_data = {
        "code": "TESTUATCOUPON",
        "discountType": "percentage",
        "discountValue": 15.0,
        "minPurchaseAmount": 200.0,
        "usageLimit": 5,
        "isActive": True,
        "validFrom": "2026-07-16T00:00:00Z",
        "validUntil": "2026-08-16T23:59:59Z"
    }

    try:
        new_coupon = await coupon_store.create(coupon_data)
        print(f"  [+] Created coupon: {new_coupon['code']} (ID: {new_coupon['_id']})")
        
        # Query database directly to check typed columns in sj_coupons_uat
        factory = get_async_session_factory()
        async with factory() as session:
            result = await session.execute(
                text("SELECT code, discount_type, discount_value, min_order_value, max_uses, is_active FROM sj_coupons_uat WHERE code = 'TESTUATCOUPON'")
            )
            row = result.fetchone()
            assert row is not None, "Coupon row not found in sj_coupons_uat table!"
            print(f"  [+] DB Direct Row: code={row[0]}, discount_type={row[1]}, discount_value={row[2]}, min_order_value={row[3]}, max_uses={row[4]}, is_active={row[5]}")
            assert row[0] == "TESTUATCOUPON", "code mismatch"
            assert row[1] == "percentage", "discount_type mismatch"
            assert float(row[2]) == 15.0, "discount_value mismatch"
            assert float(row[3]) == 200.0, "min_order_value mismatch"
            assert int(row[4]) == 5, "max_uses mismatch"
            assert int(row[5]) == 1, "is_active mismatch"
            
        # Clean up
        await coupon_store.delete(new_coupon["_id"])
        print("[+] Coupons verification completed successfully!")
    except Exception as e:
        print(f"  [-] Verification failed: {e}")
    finally:
        engine = get_async_engine()
        if engine:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
