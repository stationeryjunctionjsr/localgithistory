import json
import uuid
from datetime import datetime, timezone


def generate_id():
    return uuid.uuid4().hex


def seed():
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # 1. Users
    users = [
        {
            "_id": "user_customer_id",
            "userId": 101,
            "name": "Test Customer",
            "email": "customer@test.com",
            "role": "customer",
            "isActive": True,
            "isDeactivated": False,
            "approvalStatus": "approved",
            "creditLimit": 0.0,
            "creditUsed": 0.0,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        },
        {
            "_id": "user_retailer_id",
            "userId": 102,
            "name": "Test Retailer",
            "email": "retailer@test.com",
            "role": "retailer",
            "isActive": True,
            "isDeactivated": False,
            "approvalStatus": "approved",
            "creditLimit": 50000.0,
            "creditUsed": 0.0,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        },
        {
            "_id": "user_wholesaler_id",
            "userId": 103,
            "name": "Test Wholesaler",
            "email": "wholesaler@test.com",
            "role": "wholesaler",
            "isActive": True,
            "isDeactivated": False,
            "approvalStatus": "approved",
            "creditLimit": 100000.0,
            "creditUsed": 0.0,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        },
    ]

    # 2. Products (60 products)
    products = []
    for i in range(1, 61):
        p = {
            "_id": f"prod_{i}",
            "name": f"Product {i}",
            "sku": f"SKU-{i}",
            "category": "Stationery",
            "subCategory": "Pens" if i <= 30 else "Notebooks",
            "description": f"Description for product {i}",
            "brand": "TestBrand",
            "mrp": float(150 + i),
            "gst": 18.0,
            "mrpPerCase": None,
            "quantityPerCase": None,
            "quantityDiscounts": [],
            "stock": 100,
            "isActive": True,
            "images": ["https://via.placeholder.com/150"],
            "createdAt": now_iso,
            "updatedAt": now_iso,
            "tags": [],
            "variations": [],
        }
        products.append(p)

    # 3. Orders
    orders = []

    # Customer orders for Prod 1 (ORDER-RT starts from 1)
    for i in range(10):
        orders.append(
            {
                "_id": generate_id(),
                "orderNumber": f"ORDER-RT-{i + 1}",
                "user": "user_customer_id",
                "items": [{"product": "prod_1", "quantity": 5, "price": 101.0}],
                "status": "delivered",
                "total": 505.0,
                "createdAt": now_iso,
                "updatedAt": now_iso,
            }
        )

    # Retailer orders for Prod 2
    for i in range(10):
        orders.append(
            {
                "_id": generate_id(),
                "orderNumber": f"ORDER-RT-{i + 11}",
                "user": "user_retailer_id",
                "items": [{"product": "prod_2", "quantity": 10, "price": 102.0}],
                "status": "delivered",
                "total": 1020.0,
                "createdAt": now_iso,
                "updatedAt": now_iso,
            }
        )

    # Wholesaler orders for Prod 3 (ORDER-WH starts from 1)
    for i in range(10):
        orders.append(
            {
                "_id": generate_id(),
                "orderNumber": f"ORDER-WH-{i + 1}",
                "user": "user_wholesaler_id",
                "items": [{"product": "prod_3", "quantity": 50, "price": 103.0}],
                "status": "delivered",
                "total": 5150.0,
                "createdAt": now_iso,
                "updatedAt": now_iso,
            }
        )

    # Mixed orders for Prod 4
    for i in range(5):
        orders.append(
            {
                "_id": generate_id(),
                "orderNumber": f"ORDER-MIX-{i}",
                "user": "user_customer_id",
                "items": [{"product": "prod_4", "quantity": 2, "price": 104.0}],
                "status": "delivered",
                "total": 208.0,
                "createdAt": now_iso,
                "updatedAt": now_iso,
            }
        )

    # Save to files
    data_dir = "c:/Ecommerce app/backend/app/data"

    with open(f"{data_dir}/users.json", "w") as f:
        existing_users = [
            {
                "_id": "eaf8086f59cc2bba1f0408dcfe6d2279",
                "userId": 1,
                "name": "Super Admin",
                "email": "admin@stationery.com",
                "password": "$2a$10$FNRJ56FT/s2eKNwRhfKnXe2gpP6BTCbXCSYSPgF8gPk2/ReEAbwSO",
                "role": "super_admin",
                "isActive": True,
                "isDeactivated": False,
                "approvalStatus": "approved",
                "creditLimit": 0.0,
                "creditUsed": 0.0,
                "createdAt": now_iso,
                "updatedAt": now_iso,
            }
        ]
        json.dump(existing_users + users, f, indent=2)

    with open(f"{data_dir}/products.json", "w") as f:
        json.dump(products, f, indent=2)

    with open(f"{data_dir}/orders.json", "w") as f:
        json.dump(orders, f, indent=2)

    print("Seed data created successfully with full schema compliance!")


if __name__ == "__main__":
    seed()
