"""
Clean up the seeded Oracle database values (products and banners).
Run from the backend directory:  python scripts/delete_seeded_oracle.py
"""

import asyncio
import os
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(str(backend_root))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory

SKUS_TO_DELETE = [
    "FLAIR-WM-BLU", "CELLO-BF-BLK", "PILOT-V7-BLU", "PARKR-CL-GLD",
    "FLAIR-WM-RED", "CELLO-GRP-5P", "DOMS-Y1-10P", "DOMS-ZOOM-12",
    "NAV-LB-200R", "NAV-SB-100", "FM-A5-160SP", "BRUS-WCP-24",
    "DOMS-CP-12", "BRUS-ACR-12", "DOMS-ER-20P", "FLAIR-SH-20T",
    "ARCH-GB-DLX", "CELLO-TP-6P", "FM-SN-400", "CELLO-CALC-SC"
]

BANNERS_TO_DELETE = [
    "Back to School Sale",
    "New Arrivals - Brustro Art Supplies",
    "Bulk Order Discounts"
]

async def clean():
    factory = get_async_session_factory()
    if not factory:
        print("ERROR: DATABASE_URL not set")
        return

    async with factory() as session:
        # --- Delete Products ---
        print("Deleting seeded products...")
        result_products = await session.execute(
            text("DELETE FROM SJ_PRODUCTS WHERE sku IN :skus"),
            {"skus": tuple(SKUS_TO_DELETE)}
        )
        print(f"Deleted {result_products.rowcount} products.")

        # --- Delete Banners ---
        print("Deleting seeded banners...")
        result_banners = await session.execute(
            text("DELETE FROM SJ_BANNERS WHERE title IN :titles"),
            {"titles": tuple(BANNERS_TO_DELETE)}
        )
        print(f"Deleted {result_banners.rowcount} banners.")

        await session.commit()
        print("Successfully committed clean-up transactions!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(clean())
    print("\nClean-up complete!")
