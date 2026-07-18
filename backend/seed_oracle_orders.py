import asyncio
import os
import sys
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
from app.db.order_dao import OracleOrderDAO

async def seed_oracle():
    print("--- Seeding 20 Orders in Oracle DB ---")
    factory = get_async_session_factory()
    if not factory:
        print("ERROR: DATABASE_URL not set in env")
        return

    dao = OracleOrderDAO()

    async with factory() as session:
        # Fetch users
        print("Fetching users from sj_users...")
        res_users = await session.execute(
            text("SELECT user_id, role, email FROM sj_users WHERE is_active = 1")
        )
        users = [{"id": str(r[0]), "role": r[1], "email": r[2]} for r in res_users.fetchall()]
        print(f"Found {len(users)} active users in Oracle DB.")

        # Fetch products
        print("Fetching products from sj_products...")
        res_products = await session.execute(
            text("SELECT id, name, mrp FROM sj_products WHERE is_active = 1")
        )
        products = [{"id": str(r[0]), "name": r[1], "mrp": float(r[2]) if r[2] is not None else 10.0} for r in res_products.fetchall()]
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
            retail_users = users # fallback
        if not wholesale_users:
            wholesale_users = users # fallback

        # We will generate 20 orders.
        # Let's clean up existing orders first if any, or just add 20. Let's add 20 new ones.
        now = datetime.utcnow()

        for i in range(20):
            # Alternate between retail and wholesale
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

            order_number = await dao.generateOrderNumber(role_for_num)
            
            # Create a date in the past
            order_date = (now - timedelta(days=i, hours=i * 2)).isoformat() + "Z"

            order_data = {
                "user": user["id"],
                "userRole": role_for_num,
                "items": [
                    {
                        "product": product["id"],
                        "quantity": qty,
                        "price": price
                    }
                ],
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
                "orderNumber": order_number
            }

            print(f"Creating order {i+1}/20: {order_number} for user {user['email']} (type: {order_type})...")
            created_order = await dao.create(order_data)
            print(f"Created successfully: {created_order.get('_id') if created_order else 'None'}")

    print("\n--- Seeding Completed! ---")

if __name__ == "__main__":
    asyncio.run(seed_oracle())
