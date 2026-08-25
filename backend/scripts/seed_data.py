#!/usr/bin/env python3
"""Seed data: Create super admin and test products"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.repositories.user_repository import user_repository
from app.repositories.product_repository import product_repository


async def seed_data():
    try:
        print("=" * 60)
        print("Seeding Data: Super Admin and Test Products")
        print("=" * 60)

        # 1. Create Super Admin
        print("\n1. Creating Super Admin...")
        import os
        import secrets

        email = os.getenv("TEST_ADMIN_EMAIL", "admin@stationery.com")
        password = os.getenv("TEST_ADMIN_PASSWORD")

        existing_admin = await user_repository.findOne({"role": "super_admin"})
        if existing_admin:
            print("   ✓ Super Admin already exists")
            email = existing_admin.get("email", email)
            password = password or "(Already exists/hidden)"
            print(f"   Email: {email}")
        else:
            if not password:
                password = secrets.token_urlsafe(12)
                print(f"[*] TEST_ADMIN_PASSWORD not set. Generated secure random password: {password}")

            user_data = {
                "name": "Super Admin",
                "email": email,
                "password": password,
                "role": "super_admin",
                "isActive": True,
                "approvalStatus": "approved",
            }
            await user_repository.create(user_data)
            print("   ✓ Super Admin created successfully")
            print(f"   Email: {email}")
            print(f"   Password: {password}")

        # 2. Create Test Products
        print("\n2. Creating Test Products...")

        test_products = [
            {
                "name": "Premium Gel Pen - Blue",
                "description": "Smooth writing gel pen with blue ink. Perfect for everyday use.",
                "sku": "GEL-BLUE-001",
                "category": "Gel Pen",
                "subCategory": "Blue Ink",
                "brand": "StationeryPro",
                "mrp": 25.00,
                "mrpPerCase": None,
                "quantityPerCase": None,
                "quantityDiscounts": [],
                "stock": 500,
                "images": [],
                "tags": ["best_selling", "new"],
                "isActive": True,
            },
            {
                "name": "Ball Point Pen - Black",
                "description": "Classic ball point pen with black ink. Reliable and long-lasting.",
                "sku": "BALL-BLACK-001",
                "category": "Ball pen",
                "subCategory": "Black Ink",
                "brand": "StationeryPro",
                "mrp": 15.00,
                "mrpPerCase": None,
                "quantityPerCase": None,
                "quantityDiscounts": [],
                "stock": 800,
                "images": [],
                "tags": ["best_selling"],
                "isActive": True,
            },
            {
                "name": "Roller Pen - Red",
                "description": "Smooth roller pen with red ink. Ideal for marking and highlighting.",
                "sku": "ROLLER-RED-001",
                "category": "Roller pen",
                "subCategory": "Red Ink",
                "brand": "StationeryPro",
                "mrp": 30.00,
                "mrpPerCase": None,
                "quantityPerCase": None,
                "quantityDiscounts": [],
                "stock": 300,
                "images": [],
                "tags": ["new"],
                "isActive": True,
            },
            {
                "name": "Premium Gel Pen - Black",
                "description": "High-quality gel pen with black ink. Professional writing experience.",
                "sku": "GEL-BLACK-001",
                "category": "Gel Pen",
                "subCategory": "Black Ink",
                "brand": "StationeryPro",
                "mrp": 28.00,
                "mrpPerCase": None,
                "quantityPerCase": None,
                "quantityDiscounts": [],
                "stock": 450,
                "images": [],
                "tags": [],
                "isActive": True,
            },
            {
                "name": "Ball Point Pen - Blue",
                "description": "Smooth ball point pen with blue ink. Great for office and school use.",
                "sku": "BALL-BLUE-001",
                "category": "Ball pen",
                "subCategory": "Blue Ink",
                "brand": "StationeryPro",
                "mrp": 18.00,
                "mrpPerCase": None,
                "quantityPerCase": None,
                "quantityDiscounts": [],
                "stock": 600,
                "images": [],
                "tags": [],
                "isActive": True,
            },
        ]

        created_count = 0
        skipped_count = 0

        for product_data in test_products:
            try:
                existing = await product_repository.findBySku(product_data["sku"])
                if existing:
                    print(f"   ⚠ Product with SKU {product_data['sku']} already exists, skipping...")
                    skipped_count += 1
                else:
                    await product_repository.create(product_data)
                    print(f"   ✓ Created: {product_data['name']} ({product_data['sku']})")
                    created_count += 1
            except Exception as error:
                print(f"   ✗ Error creating {product_data['name']}: {str(error)}")

        print(f"\n   Summary: {created_count} created, {skipped_count} skipped")

        print("\n" + "=" * 60)
        print("Data Seeding Complete!")
        print("=" * 60)
        print("\nSuper Admin Credentials:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print("\n⚠ IMPORTANT: Change the password after first login!")
        print("=" * 60)

    except Exception as e:
        print(f"Error seeding data: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_data())
