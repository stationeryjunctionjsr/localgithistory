"""
Seed the Oracle database with sample stationery products, banners, and a coupon.
Run from the backend directory:  python scripts/seed_oracle.py
"""

import asyncio
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
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
NOW_ISO = datetime.now(timezone.utc)

PRODUCTS = [
    # Pens
    {
        "name": "Flair Writo-Meter Ball Pen (Blue)",
        "sku": "FLAIR-WM-BLU",
        "category": "Pen",
        "sub_category": "Ball Pen",
        "brand": "Flair",
        "mrp": 30.0,
        "stock": 500,
        "description": "0.6mm tip, 10km writing length.",
    },
    {
        "name": "Cello Butterflow Ball Pen (Black)",
        "sku": "CELLO-BF-BLK",
        "category": "Pen",
        "sub_category": "Ball Pen",
        "brand": "Cello",
        "mrp": 20.0,
        "stock": 800,
        "description": "Smooth butterflow ink for everyday writing.",
    },
    {
        "name": "Pilot V7 Hi-Tecpoint (Blue)",
        "sku": "PILOT-V7-BLU",
        "category": "Pen",
        "sub_category": "Gel Pen",
        "brand": "Pilot",
        "mrp": 120.0,
        "stock": 200,
        "description": "0.7mm liquid ink roller pen with fine tip.",
    },
    {
        "name": "Parker Classic Gold Trim Ball Pen",
        "sku": "PARKR-CL-GLD",
        "category": "Pen",
        "sub_category": "Ball Pen",
        "brand": "Parker",
        "mrp": 350.0,
        "stock": 50,
        "description": "Classic matte black with gold trim.",
    },
    {
        "name": "Flair Writometer Gel Pen (Red)",
        "sku": "FLAIR-WM-RED",
        "category": "Pen",
        "sub_category": "Gel Pen",
        "brand": "Flair",
        "mrp": 35.0,
        "stock": 350,
        "description": "Red gel ink, 0.5mm needle tip.",
    },
    {
        "name": "Cello Gripper Ball Pen Pack of 5",
        "sku": "CELLO-GRP-5P",
        "category": "Pen",
        "sub_category": "Ball Pen",
        "brand": "Cello",
        "mrp": 75.0,
        "stock": 400,
        "description": "Comfortable rubber grip, assorted colours.",
    },
    # Pencils
    {
        "name": "Doms Y1+ Pencil Pack of 10",
        "sku": "DOMS-Y1-10P",
        "category": "Writing Pencil",
        "sub_category": "HB Pencil",
        "brand": "Doms",
        "mrp": 60.0,
        "stock": 600,
        "description": "Dark writing, easy to sharpen.",
    },
    {
        "name": "Doms Zoom Ultimate Dark Pencil",
        "sku": "DOMS-ZOOM-12",
        "category": "Writing Pencil",
        "sub_category": "HB Pencil",
        "brand": "Doms",
        "mrp": 80.0,
        "stock": 450,
        "description": "Extra dark graphite for exams.",
    },
    # Notebooks
    {
        "name": "Navneet Long Book 200 Pages Ruled",
        "sku": "NAV-LB-200R",
        "category": "Notebooks",
        "sub_category": "Long Book",
        "brand": "Navneet",
        "mrp": 90.0,
        "stock": 300,
        "description": "Single line ruled, standard long notebook.",
    },
    {
        "name": "Navneet Short Book 100 Pages",
        "sku": "NAV-SB-100",
        "category": "Notebooks",
        "sub_category": "Short Book",
        "brand": "Navneet",
        "mrp": 40.0,
        "stock": 500,
        "description": "Small notebook for quick notes.",
    },
    {
        "name": "Freemind A5 Spiral Notebook 160 Pages",
        "sku": "FM-A5-160SP",
        "category": "Notebooks",
        "sub_category": "Spiral Notebook",
        "brand": "Freemind",
        "mrp": 150.0,
        "stock": 250,
        "description": "Perforated sheets, 5-subject dividers.",
    },
    # Art supplies
    {
        "name": "Brustro Artists Watercolour Pencils Set of 24",
        "sku": "BRUS-WCP-24",
        "category": "Art Pencils",
        "sub_category": "Colour Pencil",
        "brand": "Brustro",
        "mrp": 650.0,
        "stock": 80,
        "description": "Professional water-soluble colour pencils.",
    },
    {
        "name": "Doms Colour Pencils Pack of 12",
        "sku": "DOMS-CP-12",
        "category": "Art Pencils",
        "sub_category": "Colour Pencil",
        "brand": "Doms",
        "mrp": 55.0,
        "stock": 700,
        "description": "Bright colours, break resistant leads.",
    },
    {
        "name": "Brustro Acrylic Paint Set of 12",
        "sku": "BRUS-ACR-12",
        "category": "Art Supplies",
        "sub_category": "Acrylic Paint",
        "brand": "Brustro",
        "mrp": 450.0,
        "stock": 60,
        "description": "12 vibrant acrylic colours, 12ml tubes each.",
    },
    # Erasers / Sharpeners
    {
        "name": "Doms Non-Dust Eraser Pack of 20",
        "sku": "DOMS-ER-20P",
        "category": "Eraser",
        "sub_category": None,
        "brand": "Doms",
        "mrp": 50.0,
        "stock": 1000,
        "description": "Dust-free, PVC-free erasers.",
    },
    {
        "name": "Flair Sharpener Tub (Pack of 20)",
        "sku": "FLAIR-SH-20T",
        "category": "Sharpener",
        "sub_category": None,
        "brand": "Flair",
        "mrp": 100.0,
        "stock": 400,
        "description": "Round tub sharpener, collects shavings.",
    },
    # Other stationery
    {
        "name": "Archies Geometry Box Deluxe",
        "sku": "ARCH-GB-DLX",
        "category": "Geometry Box",
        "sub_category": None,
        "brand": "Archies",
        "mrp": 180.0,
        "stock": 200,
        "description": "Metal box with compass, divider, protractor and set squares.",
    },
    {
        "name": "Cello Tape 1 inch 65m (Pack of 6)",
        "sku": "CELLO-TP-6P",
        "category": "Cello Tape",
        "sub_category": None,
        "brand": "Cello",
        "mrp": 120.0,
        "stock": 350,
        "description": "BOPP self-adhesive transparent tape.",
    },
    {
        "name": "Freemind Sticky Notes 3x3 inch 400 Sheets",
        "sku": "FM-SN-400",
        "category": "Sticky Note",
        "sub_category": None,
        "brand": "Freemind",
        "mrp": 120.0,
        "stock": 500,
        "description": "Neon assorted colours, re-stickable.",
    },
    {
        "name": "Cello Scientific Calculator",
        "sku": "CELLO-CALC-SC",
        "category": "Calculator",
        "sub_category": None,
        "brand": "Cello",
        "mrp": 350.0,
        "stock": 120,
        "description": "240 functions, dual power.",
    },
]

BANNERS = [
    {
        "title": "Back to School Sale",
        "description": "Up to 30% off on notebooks, pens and more!",
        "image_url": "https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?w=800",
        "link_url": "/categories",
        "position": "home_top",
        "display_order": 1,
    },
    {
        "title": "New Arrivals - Brustro Art Supplies",
        "description": "Professional grade art materials now available",
        "image_url": "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=800",
        "link_url": "/brands",
        "position": "home_top",
        "display_order": 2,
    },
    {
        "title": "Bulk Order Discounts",
        "description": "Special wholesale prices for businesses and schools",
        "image_url": "https://images.unsplash.com/photo-1456735190827-d1262f71b8a3?w=800",
        "link_url": "/products",
        "position": "home_top",
        "display_order": 3,
    },
]


async def seed():
    factory = get_async_session_factory()
    if not factory:
        print("ERROR: DATABASE_URL not set")
        return

    async with factory() as session:
        # --- Activate existing test products ---
        await session.execute(text("UPDATE SJ_PRODUCTS SET is_active = 1"))
        print("Activated existing products")

        # --- Seed products ---
        inserted = 0
        for p in PRODUCTS:
            eid = secrets.token_hex(16)
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
                    "eid": eid,
                    "name": p["name"],
                    "desc": p.get("description"),
                    "sku": p["sku"],
                    "cat": p["category"],
                    "sub": p.get("sub_category"),
                    "brand": p["brand"],
                    "mrp": p["mrp"],
                    "mrp_per_case": None,
                    "quantity_per_case": None,
                    "stock": p.get("stock", 100),
                    "images": json_dumps(
                        ["https://via.placeholder.com/400x400.png?text=" + p["name"].replace(" ", "+")]
                    ),
                    "videos": json_dumps([]),
                    "tags": json_dumps([]),
                    "va": json_dumps([]),
                    "vc": json_dumps([]),
                    "details": json_dumps({}),
                    "now": NOW,
                },
            )
            inserted += 1
        print(f"Inserted {inserted} products")

        # --- Seed banners ---
        for b in BANNERS:
            eid = secrets.token_hex(16)
            await session.execute(
                text("""
                    INSERT INTO SJ_BANNERS (
                        external_id, title, description, image_url, link_url,
                        display_order, start_date, end_date,
                        is_active, is_published, target_audience, position,
                        user_segments, visibility_rules, created_at, updated_at
                    ) VALUES (
                        :eid, :title, :desc, :img, :link,
                        :order, NULL, NULL,
                        1, 1, :audience, :pos,
                        :segs, :rules, :now, :now
                    )
                """),
                {
                    "eid": eid,
                    "title": b["title"],
                    "desc": b["description"],
                    "img": b["image_url"],
                    "link": b["link_url"],
                    "order": b["display_order"],
                    "audience": "all",
                    "pos": b["position"],
                    "segs": json_dumps([]),
                    "rules": json_dumps([]),
                    "now": NOW,
                },
            )
        print(f"Inserted {len(BANNERS)} banners")

        await session.commit()
        print("Committed all data")

    # Verify
    async with factory() as session:
        r = await session.execute(text("SELECT COUNT(*) FROM SJ_PRODUCTS WHERE is_active = 1"))
        print(f"\nVerification: {r.scalar()} active products")
        r2 = await session.execute(text("SELECT COUNT(*) FROM SJ_BANNERS WHERE is_active = 1"))
        print(f"Verification: {r2.scalar()} active banners")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())
    print("\nDone! Restart Metro or refresh the app to see the data.")
