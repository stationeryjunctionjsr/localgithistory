import json
import os
from datetime import datetime, timedelta
from uuid import uuid4

ORDERS_FILE = "app/data/orders.json"
PRODUCTS_FILE = "app/data/products.json"


def seed_orders():
    print("--- Seeding Orders for Best Seller Verification ---")

    # Load products to get ID
    with open(PRODUCTS_FILE, "r") as f:
        products = json.load(f)

    flair_pen = next((p for p in products if p["name"] == "Flair Pen"), None)
    if not flair_pen:
        print("Flair Pen not found!")
        return

    product_id = flair_pen["_id"]
    now = datetime.utcnow().isoformat() + "Z"

    orders = []

    # 1. 10 Customer orders (ORDER-RT)
    for i in range(10):
        orders.append(
            {
                "_id": str(uuid4()).replace("-", "")[:32],
                "orderNumber": f"ORDER-RT-{i + 1000}",
                "items": [{"product": product_id, "quantity": 1}],
                "status": "delivered",
                "createdAt": now,
                "updatedAt": now,
            }
        )

    # 2. 5 Retailer orders (RT)
    for i in range(5):
        orders.append(
            {
                "_id": str(uuid4()).replace("-", "")[:32],
                "orderNumber": f"ORDER-RT-{i + 2000}",
                "items": [{"product": product_id, "quantity": 1}],
                "status": "delivered",
                "createdAt": now,
                "updatedAt": now,
            }
        )

    # 3. 2 Wholesaler orders (WH)
    for i in range(2):
        orders.append(
            {
                "_id": str(uuid4()).replace("-", "")[:32],
                "orderNumber": f"ORDER-WH-{i + 3000}",
                "items": [{"product": product_id, "quantity": 1}],
                "status": "delivered",
                "createdAt": now,
                "updatedAt": now,
            }
        )

    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)

    print(f"Successfully seeded {len(orders)} orders.")


if __name__ == "__main__":
    seed_orders()
