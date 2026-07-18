import json
import os
import uuid
from datetime import datetime, timedelta, timezone

ORDERS_FILE = "app/data/orders.json"
PRODUCTS_FILE = "app/data/products.json"
USERS_FILE = "app/data/users.json"

def seed_20_orders():
    print("--- Seeding 20 Real Orders ---")
    
    # Resolve paths relative to backend directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    orders_path = os.path.join(base_dir, "app", "data", "orders.json")
    products_path = os.path.join(base_dir, "app", "data", "products.json")
    users_path = os.path.join(base_dir, "app", "data", "users.json")

    # Load users
    with open(users_path, "r", encoding="utf-8") as f:
        users = json.load(f)
    
    # Load products
    with open(products_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    if not users or not products:
        print("Missing users or products to seed orders.")
        return

    # Find candidate users and products
    customers = [u for u in users if u.get("role") == "customer"]
    wholesalers = [u for u in users if u.get("role") == "wholesaler"]
    
    if not customers:
        customers = users[:1]
    if not wholesalers:
        wholesalers = users[:1]

    # Let's generate 20 orders
    orders = []
    now = datetime.now(timezone.utc)

    # 12 customer orders
    for i in range(12):
        user = customers[i % len(customers)]
        product = products[i % len(products)]
        qty = (i % 3) + 1
        price = product.get("mrp", 10.0)
        subtotal = price * qty
        tax = round(subtotal * 0.18, 2)
        shipping = 50.0 if subtotal < 500 else 0.0
        total = subtotal + tax + shipping

        order_id = uuid.uuid4().hex
        order_num = f"ORDER-RT-{1000 + i}"
        order_date = (now - timedelta(days=i, hours=i*2)).isoformat().replace("+00:00", "Z")

        orders.append({
            "_id": order_id,
            "orderNumber": order_num,
            "user": user["_id"],
            "items": [
                {
                    "product": product["_id"],
                    "quantity": qty,
                    "price": price
                }
            ],
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "discount": 0.0,
            "total": total,
            "orderType": "retail",
            "status": "delivered" if i > 2 else "pending",
            "paymentStatus": "paid" if i > 2 else "pending",
            "paymentMethod": "cod",
            "createdAt": order_date,
            "updatedAt": order_date
        })

    # 8 wholesaler orders
    for i in range(8):
        user = wholesalers[i % len(wholesalers)]
        product = products[i % len(products)]
        qty = (i + 1) * 10
        price = product.get("mrp", 10.0) * 0.8 # Wholesale discount
        subtotal = price * qty
        tax = round(subtotal * 0.18, 2)
        shipping = 0.0
        total = subtotal + tax + shipping

        order_id = uuid.uuid4().hex
        order_num = f"ORDER-WH-{2000 + i}"
        order_date = (now - timedelta(days=i, hours=i*3)).isoformat().replace("+00:00", "Z")

        orders.append({
            "_id": order_id,
            "orderNumber": order_num,
            "user": user["_id"],
            "items": [
                {
                    "product": product["_id"],
                    "quantity": qty,
                    "price": price
                }
            ],
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "discount": 0.0,
            "total": total,
            "orderType": "wholesale",
            "status": "delivered" if i > 1 else "pending",
            "paymentStatus": "paid" if i > 1 else "pending",
            "paymentMethod": "net_30",
            "createdAt": order_date,
            "updatedAt": order_date
        })

    # Write back to files
    with open(orders_path, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2)

    print(f"Successfully seeded {len(orders)} orders into {orders_path}.")

if __name__ == "__main__":
    seed_20_orders()
