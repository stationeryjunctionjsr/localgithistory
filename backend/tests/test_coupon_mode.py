import pytest
import uuid
from app.repositories.product_repository import product_repository
from app.repositories.coupon_repository import coupon_repository


@pytest.mark.asyncio
async def test_coupon_override_and_stacking():
    # Pre-test cleanup: delete product/coupons if they already exist
    existing_product = await product_repository.findBySku("SKU-TEST-COUPON-MODE")
    if existing_product:
        await product_repository.storage.delete(existing_product.id if hasattr(product, "id") else product["_id"])

    existing_override = await coupon_repository.findByCode("OVERRIDE10")
    if existing_override:
        await coupon_repository.storage.delete(existing_override["_id"])

    existing_extra = await coupon_repository.findByCode("EXTRA10")
    if existing_extra:
        await coupon_repository.storage.delete(existing_extra["_id"])

    # 1. Create a test product
    product_data = {
        "name": "Test Coupon Mode Product",
        "category": "Test Category",
        "mrp": 100.0,
        "sku": "SKU-TEST-COUPON-MODE",
        "isActive": True,
    }
    product = await product_repository.create(product_data)
    product_id = str(product.id if hasattr(product, "id") else product["_id"])

    # 2. Create an automatic product discount (15% off)
    auto_discount_data = {
        "typeOfDiscount": "product_discount",
        "method": "automatic",
        "discountType": "percentage",
        "discountValue": 15.0,
        "isActive": True,
        "validFrom": "2026-01-01T00:00:00",
        "validUntil": "2026-12-31T23:59:59",
        "applicableRoles": ["customer"],
        "appliesToType": "products",
        "appliesToValueIds": [product_id],
        "force": True,
    }
    auto_coupon = await coupon_repository.create(auto_discount_data)
    print("Created auto coupon:", auto_coupon)

    from sqlalchemy import text
    factory = coupon_repository.storage._factory()
    async with factory() as session:
        result = await session.execute(text(f"SELECT id, extra_data FROM sj_coupons WHERE id={auto_coupon['_id']}"))
        print("Raw SQL row:", result.fetchone())

    # 3. Create an override coupon code (10% off)
    override_coupon_data = {
        "typeOfDiscount": "product_discount",
        "method": "discount_code",
        "code": "OVERRIDE10",
        "discountType": "percentage",
        "discountValue": 10.0,
        "couponMode": "override",
        "isActive": True,
        "validFrom": "2026-01-01T00:00:00",
        "validUntil": "2026-12-31T23:59:59",
        "applicableRoles": ["customer"],
        "appliesToType": "products",
        "appliesToValueIds": [product_id],
        "force": True,
    }
    override_coupon = await coupon_repository.create(override_coupon_data)

    # 4. Create an extra/stacking coupon code (10% off)
    extra_coupon_data = {
        "typeOfDiscount": "product_discount",
        "method": "discount_code",
        "code": "EXTRA10",
        "discountType": "percentage",
        "discountValue": 10.0,
        "couponMode": "extra",
        "isActive": True,
        "validFrom": "2026-01-01T00:00:00",
        "validUntil": "2026-12-31T23:59:59",
        "applicableRoles": ["customer"],
        "appliesToType": "products",
        "appliesToValueIds": [product_id],
        "force": True,
    }
    extra_coupon = await coupon_repository.create(extra_coupon_data)

    try:
        # Force reload active automatic product discounts cache
        coupon_repository._active_automatic_discounts_cache = None
        coupon_repository._active_automatic_discounts_cache_time = None
        
        discounts = await coupon_repository.get_active_automatic_product_discounts()
        print("Auto discounts found:", len(discounts))
        print("Auto coupon id:", product_id)
        for c in discounts:
            print("Discount:", c.get("method"), c.get("isActive"), c.get("typeOfDiscount"), c.get("appliesToValueIds"))

        # Normal price calculation should apply the 15% automatic discount -> 85.0
        price_normal = product_repository.getPriceForRole(product, "customer", quantity=1)
        assert price_normal == 85.0

        # OVERRIDE coupon code ignores the 15% automatic discount and applies 10% on MRP (100.0) -> 10.0 discount.
        validation_override = await coupon_repository.validateCoupon(
            "OVERRIDE10",
            "customer",
            0.0,
            "test_user",
            cart_items=[{"product": product_id, "quantity": 1}],
            product_repository=product_repository,
        )
        assert validation_override["valid"] is True
        assert validation_override["discount"] == 10.0

        # EXTRA coupon code stacks on top of 15% automatic discount (price is 85.0) and applies 10% -> 8.5 discount.
        validation_extra = await coupon_repository.validateCoupon(
            "EXTRA10",
            "customer",
            0.0,
            "test_user",
            cart_items=[{"product": product_id, "quantity": 1}],
            product_repository=product_repository,
        )
        assert validation_extra["valid"] is True
        assert validation_extra["discount"] == 8.5

    finally:
        # Cleanup db
        await product_repository.storage.delete(product.id if hasattr(product, "id") else product["_id"])
        await coupon_repository.storage.delete(auto_coupon["_id"])
        await coupon_repository.storage.delete(override_coupon["_id"])
        await coupon_repository.storage.delete(extra_coupon["_id"])
        coupon_repository._active_automatic_discounts_cache = None
        coupon_repository._active_automatic_discounts_cache_time = None
