import asyncio
import os
import sys
import json
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Load backend root
backend_root = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)
load_dotenv()

from app.config.database import get_async_session_factory
from app.db.product_dao import OracleProductDAO
from app.repositories.order_repository import order_repository


async def sync_and_seed():
    print("--- Syncing Products & Seeding 20 Orders in Oracle DB ---")
    factory = get_async_session_factory()
    if not factory:
        print("ERROR: DATABASE_URL not set in env")
        return

    # 1. Sync Products from products.json
    products_file_path = os.path.join("app", "data", "products.json")
    if os.path.exists(products_file_path):
        with open(products_file_path, "r", encoding="utf-8") as f:
            local_products = json.load(f)
    else:
        local_products = []

    print(f"Loaded {len(local_products)} products from local JSON file.")

    product_dao = OracleProductDAO()
    async with factory() as session:
        # Check if Oracle sj_products is empty
        r = await session.execute(text("SELECT count(*) FROM sj_products"))
        oracle_prod_count = r.fetchone()[0]
        print(f"Current product count in Oracle: {oracle_prod_count}")

        if oracle_prod_count == 0 and local_products:
            print("Oracle products table is empty. Seeding products from products.json...")
            for lp in local_products:
                # Map keys to correct format for Oracle
                prod_data = {
                    "name": lp.get("name"),
                    "description": lp.get("description", ""),
                    "sku": lp.get("sku"),
                    "category": lp.get("category"),
                    "subCategory": lp.get("subCategory"),
                    "brand": lp.get("brand"),
                    "mrp": lp.get("mrp"),
                    "mrpPerCase": lp.get("mrpPerCase"),
                    "quantityPerCase": lp.get("quantityPerCase"),
                    "stock": lp.get("stock", 100)
                    if lp.get("stock", 0) > 0
                    else 100,  # ensure we have stock for ordering
                    "images": lp.get("images", []),
                    "videos": lp.get("videos", []),
                    "isActive": lp.get("isActive", True),
                    "tags": lp.get("tags", []),
                    "variantAttributes": lp.get("variantAttributes", []),
                    "variantCombinations": lp.get("variantCombinations", []),
                    "details": lp.get("details", {}),
                }
                created_p = await product_dao.create(prod_data)
                print(f"Created product in Oracle: {created_p.get('name')} (ID: {created_p.get('_id')})")
        else:
            print("Oracle already has products or products.json is missing.")

    # 2. Seed 20 Orders
    async with factory() as session:
        # Fetch users
        print("Fetching users from sj_users...")
        res_users = await session.execute(text("SELECT user_id, role, email FROM sj_users WHERE is_active = 1"))
        users = [{"id": str(r[0]), "role": r[1], "email": r[2]} for r in res_users.fetchall()]
        print(f"Found {len(users)} active users in Oracle DB.")

        # Fetch products (now loaded)
        print("Fetching products from sj_products...")
        res_products = await session.execute(text("SELECT id, name, mrp FROM sj_products WHERE is_active = 1"))
        products = [
            {"id": str(r[0]), "name": r[1], "mrp": float(r[2]) if r[2] is not None else 10.0}
            for r in res_products.fetchall()
        ]
        print(f"Found {len(products)} active products in Oracle DB.")

        if not users:
            print("ERROR: No active users found in sj_users. Cannot seed orders.")
            return
        if not products:
            print("ERROR: No active products found in sj_products. Cannot seed orders.")
            return

        # Separate retail and wholesale customers
        retail_users = [u for u in users if u["role"] in ("customer", "super_admin")]
        wholesale_users = [u for u in users if u["role"] == "wholesaler"]

        if not retail_users:
            retail_users = users
        if not wholesale_users:
            wholesale_users = users

        now = datetime.now(timezone.utc)

        for i in range(20):
            is_wholesale = (i % 2 == 1) and len(wholesale_users) > 0

            if is_wholesale:
                user = wholesale_users[i % len(wholesale_users)]
                order_type = "wholesale"
                payment_method = "net_30"
                role_for_num = "wholesaler"
            else:
                user = retail_users[i % len(retail_users)]
                order_type = "retail"
                payment_method = "cod"
                role_for_num = "customer"

            product = products[i % len(products)]
            qty = (i % 3) + 1 if not is_wholesale else (i + 1) * 5
            price = product["mrp"] if not is_wholesale else round(product["mrp"] * 0.8, 2)
            subtotal = price * qty
            tax = round(subtotal * 0.18, 2)
            shipping = 50.0 if (subtotal < 500 and not is_wholesale) else 0.0
            total = subtotal + tax + shipping

            order_date = (now - timedelta(days=i, hours=i * 2)).isoformat().replace("+00:00", "Z")

            order_data = {
                "user": user["id"],
                "userRole": role_for_num,
                "items": [{"product": product["id"], "quantity": qty, "price": price}],
                "subtotal": subtotal,
                "tax": tax,
                "shipping": shipping,
                "discount": 0.0,
                "total": total,
                "orderType": order_type,
                "status": "delivered" if i > 4 else "pending",
                "paymentStatus": "paid" if i > 4 else "pending",
                "paymentMethod": payment_method,
                "createdAt": order_date,
            }

            print(f"Creating order {i + 1}/20 for user {user['email']} (type: {order_type})...")
            created_order = await order_repository.create(order_data)
            print(f"Created successfully: {created_order.get('orderNumber') if created_order else 'None'}")

    print("\n--- Syncing and Seeding Completed! ---")


if __name__ == "__main__":
    asyncio.run(sync_and_seed())
