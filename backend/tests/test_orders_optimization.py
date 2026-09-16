import pytest
from httpx import AsyncClient
from app.repositories.order_repository import order_repository
from app.repositories.product_repository import product_repository
from app.repositories.user_repository import user_repository
from app.repositories.payment_repository import payment_repository
from app.routers.orders import populate_orders, populate_order


async def clean_database():
    try:
        # Delete test orders
        orders = await order_repository.storage.findAll()
        for o in orders:
            if getattr(o, "notes", "") or "".startswith("TEST_ORDER_OPT_") or getattr(o, "notes", "") or "".startswith(
                "Referral Code Applied: TEST_ORDER_OPT_"
            ):
                await order_repository.storage.delete(getattr(o, "id", getattr(o, "_id", None)))

        # Delete test payments
        payments = await payment_repository.storage.findAll()
        for p in payments:
            if getattr(p, "customer_name", getattr(p, "customerName", None)) == "TEST_ORDER_OPT_User":
                await payment_repository.storage.delete(getattr(p, "id", getattr(p, "_id", None)))

        # Delete test user
        users = await user_repository.findAll()
        for u in users:
            if getattr(u, "name", None) == "TEST_ORDER_OPT_User" or getattr(u, "email", None) == "opt_user@test.com":
                await user_repository.delete(getattr(u, "id", getattr(u, "_id", None)))

        # Delete test product
        products = await product_repository.findAll()
        for p in products:
            if getattr(p, "name", None) == "TEST_ORDER_OPT_Product" or getattr(p, "sku", None) == "SKU-OPT-123":
                await product_repository.storage.delete(getattr(p, "id", getattr(p, "_id", None)))
    except Exception:
        pass


@pytest.fixture(autouse=True)
async def cleanup_orders():
    await clean_database()
    yield
    await clean_database()


@pytest.mark.asyncio
async def test_orders_optimization_logic():
    # 1. Create a test user, product, and payment
    user = await user_repository.create(
        {"name": "TEST_ORDER_OPT_User", "email": "opt_user@test.com", "password": "Password123", "role": "customer"}
    )

    product = await product_repository.create(
        {"name": "TEST_ORDER_OPT_Product", "sku": "SKU-OPT-123", "mrp": 100.0, "category": "Stationery"}
    )

    # 2. Create order
    order = await order_repository.create(
        {
            "user": user["_id"],
            "userRole": "customer",
            "items": [{"product": product.id if hasattr(product, "id") else product["_id"], "quantity": 2, "price": 100.0}],
            "subtotal": 200.0,
            "total": 200.0,
            "orderType": "b2c",
            "paymentMethod": "cod",
            "shippingAddress": {"zipCode": "110001"},
            "notes": "TEST_ORDER_OPT_Note",
        }
    )

    # Create associated payment
    payment = await payment_repository.create(
        {
            "orderId": order["_id"],
            "userId": user["_id"],
            "customerName": "TEST_ORDER_OPT_User",
            "paymentMethod": "cod",
            "totalAmount": 200.0,
            "paymentEntries": [{"entryId": 1, "amount": 200.0, "verified": False}],
        }
    )

    # 3. Test populate_orders batch loader
    populated = await populate_orders([order])
    assert len(populated) == 1
    assert populated[0]["user"]["name"] == "TEST_ORDER_OPT_User"
    assert populated[0]["items"][0]["product"]["name"] == "TEST_ORDER_OPT_Product"
    assert len(populated[0]["paymentEntries"]) == 1
    assert populated[0]["paymentEntries"][0]["amount"] == 200.0

    # 4. Test populate_order single wrapper
    single_populated = await populate_order(order)
    assert single_populated is not None
    assert single_populated["user"]["name"] == "TEST_ORDER_OPT_User"

    # 5. Test findByOrderId query offloading
    found_payments = await payment_repository.findByOrderId(order["_id"])
    assert len(found_payments) == 1
    assert found_payments[0]["_id"] == payment["_id"]


@pytest.mark.asyncio
async def test_orders_pagination_and_counting_logic():
    # 1. Create a test user and product
    user = await user_repository.create(
        {"name": "TEST_ORDER_OPT_User", "email": "opt_user@test.com", "password": "Password123", "role": "customer"}
    )

    product = await product_repository.create(
        {"name": "TEST_ORDER_OPT_Product", "sku": "SKU-OPT-123", "mrp": 100.0, "category": "Stationery"}
    )

    # 2. Create 3 test orders with unique notes and payment methods
    o1 = await order_repository.create(
        {
            "user": user["_id"],
            "userRole": "customer",
            "items": [{"product": product.id if hasattr(product, "id") else product["_id"], "quantity": 1, "price": 100.0}],
            "subtotal": 100.0,
            "total": 100.0,
            "orderType": "b2c",
            "paymentMethod": "cod",
            "shippingAddress": {"zipCode": "110001"},
            "notes": "TEST_ORDER_OPT_1",
        }
    )
    o2 = await order_repository.create(
        {
            "user": user["_id"],
            "userRole": "customer",
            "items": [{"product": product.id if hasattr(product, "id") else product["_id"], "quantity": 1, "price": 100.0}],
            "subtotal": 100.0,
            "total": 100.0,
            "orderType": "b2c",
            "paymentMethod": "upi",
            "shippingAddress": {"zipCode": "110001"},
            "notes": "TEST_ORDER_OPT_2",
        }
    )
    o3 = await order_repository.create(
        {
            "user": user["_id"],
            "userRole": "customer",
            "items": [{"product": product.id if hasattr(product, "id") else product["_id"], "quantity": 1, "price": 100.0}],
            "subtotal": 100.0,
            "total": 100.0,
            "orderType": "b2c",
            "paymentMethod": "cod",
            "shippingAddress": {"zipCode": "110001"},
            "notes": "TEST_ORDER_OPT_3",
        }
    )

    # 3. Test count directly
    total_count = await order_repository.count({"user": user["_id"]})
    assert total_count == 3

    # Test count by user helper
    count_by_user = await order_repository.countByUser(user["_id"])
    assert count_by_user == 3

    # Test count with filtering by paymentMethod
    cod_count = await order_repository.count({"user": user["_id"], "paymentMethod": "cod"})
    assert cod_count == 2
    upi_count = await order_repository.count({"user": user["_id"], "paymentMethod": "upi"})
    assert upi_count == 1

    # 4. Test database-level pagination in findAll
    # Page 1: limit 2
    p1 = await order_repository.findAll({"user": user["_id"]}, skip=0, limit=2)
    assert len(p1) == 2
    # Page 2: limit 2
    p2 = await order_repository.findAll({"user": user["_id"]}, skip=2, limit=2)
    assert len(p2) == 1

    # Verify that the order IDs in pagination correspond to the correct order of created_at desc
    # (since the newest order is created last, it should be first in results)
    ids_p1 = [getattr(o, "id", getattr(o, "_id", None)) for o in p1]
    ids_p2 = [getattr(o, "id", getattr(o, "_id", None)) for o in p2]

    assert o3["_id"] in ids_p1
    assert o2["_id"] in ids_p1
    assert o1["_id"] in ids_p2
