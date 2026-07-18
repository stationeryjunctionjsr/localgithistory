import asyncio
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(str(backend_root))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.oracle_utils import json_dumps, now_utc

NOW = now_utc()

async def create_product():
    factory = get_async_session_factory()
    if not factory:
        print("ERROR: DATABASE_URL not set")
        return

    async with factory() as session:
        eid = secrets.token_hex(16)
        product = {
            "name": "Test Premium Notebook (All Fields)",
            "description": "This is a test product with all fields filled. High quality 200 pages ruled notebook for professionals.",
            "sku": f"TEST-NB-{secrets.token_hex(4).upper()}",
            "category": "Notebooks",
            "sub_category": "Long Book",
            "brand": "Navneet",
            "mrp": 199.0,
            "mrp_per_case": 1990.0,
            "quantity_per_case": 10,
            "stock": 50,
            "images": ["https://images.unsplash.com/photo-1531346878377-a541e4b115b7?w=800"],
            "videos": [],
            "tags": ["notebook", "test", "premium", "ruled"],
            "va": [],
            "vc": [],
            "details": {"Color": "Black", "Pages": "200", "Material": "Premium Paper"}
        }

        await session.execute(
            text("""
                INSERT INTO SJ_PRODUCTS (
                    external_id, name, description, sku, category, sub_category, brand,
                    mrp, mrp_per_case, quantity_per_case,
                    stock, images, videos,
                    is_active, tags, variant_attributes,
                    variant_combinations, details, created_at, updated_at
                ) VALUES (
                    :eid, :name, :desc, :sku, :cat, :sub, :brand,
                    :mrp, :mrp_per_case, :quantity_per_case,
                    :stock, :images, :videos,
                    1, :tags, :va,
                    :vc, :details, :now, :now
                )
            """),
            {
                "eid": eid, "name": product["name"], "desc": product["description"],
                "sku": product["sku"], "cat": product["category"], "sub": product["sub_category"],
                "brand": product["brand"], "mrp": product["mrp"],
                "mrp_per_case": product["mrp_per_case"], "quantity_per_case": product["quantity_per_case"],
                "stock": product["stock"],
                "images": json_dumps(product["images"]),
                "videos": json_dumps(product["videos"]),
                "tags": json_dumps(product["tags"]),
                "va": json_dumps(product["va"]),
                "vc": json_dumps(product["vc"]),
                "details": json_dumps(product["details"]),
                "now": NOW,
            },
        )
        await session.commit()
        
        # Get the ID to return
        r = await session.execute(text("SELECT id, external_id FROM SJ_PRODUCTS WHERE sku = :sku"), {"sku": product["sku"]})
        row = r.fetchone()
        product_id = row[0]
        print(f"Test product created! ID: {product_id}, SKU: {product['sku']}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_product())
