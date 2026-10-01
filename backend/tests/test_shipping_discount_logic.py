try:
    from app.models.daos import CouponInternalCreate
except ImportError:
    pass
try:
    from app.models.daos_flat import CouponInternalCreate
except ImportError:
    pass
import pytest
from app.repositories.product_repository import product_repository
from app.repositories.coupon_repository import coupon_repository


@pytest.mark.asyncio
async def test_shipping_discount_payment_method_and_capping():
    # 1. Cleanup existing coupon if any
    existing_coupon = await coupon_repository.findByCode("SHIPUPI50")
    if existing_coupon:
        await coupon_repository.storage.delete(existing_coupon["_id"])

    # 2. Create a shipping discount coupon: 50% off shipping, UPI payment only
    ship_coupon = await coupon_repository.create(
        CouponInternalCreate(**{'_id': __import__('uuid').uuid4().hex, **{
            "typeOfDiscount": "shipping_discount",
            "method": "discount_code",
            "code": "SHIPUPI50",
            "isActive": True,
            "validFrom": "2026-01-01T00:00:00",
            "validUntil": "2026-12-31T23:59:59",
            "applicableRoles": ["customer"],
            "discountType": "percentage",
            "discountValue": 50.0,
            "applicablePaymentMethods": ["upi"],
            "appliesToType": "all",
            "force": True,
        }})
    )

    # 3. Create a fixed shipping discount coupon: Rs. 100 off shipping, UPI payment only
    existing_fixed = await coupon_repository.findByCode("SHIPFIXED100")
    if existing_fixed:
        await coupon_repository.storage.delete(existing_fixed["_id"])

    fixed_coupon = await coupon_repository.create(
        CouponInternalCreate(**{'_id': __import__('uuid').uuid4().hex, **{
            "typeOfDiscount": "shipping_discount",
            "method": "discount_code",
            "code": "SHIPFIXED100",
            "isActive": True,
            "validFrom": "2026-01-01T00:00:00",
            "validUntil": "2026-12-31T23:59:59",
            "applicableRoles": ["customer"],
            "discountType": "fixed",
            "discountValue": 100.0,
            "applicablePaymentMethods": ["upi"],
            "appliesToType": "all",
            "force": True,
        }})
    )

    mock_address = {
        "zipCode": "123456",
        "street": "123 Main St",
        "city": "City",
        "state": "State",
        "district": "District",
    }

    try:
        # Test Case A: Validate coupon with wrong payment method (cod instead of upi)
        validation_cod = await coupon_repository.validateCoupon(
            "SHIPUPI50",
            "customer",
            500.0,
            "test_user",
            payment_method="cod",
            shipping_charge=80.0,
            shipping_address=mock_address,
        )
        assert validation_cod["valid"] is False
        assert "payment method" in validation_cod["message"].lower()

        # Test Case B: Validate coupon with correct payment method (upi)
        validation_upi = await coupon_repository.validateCoupon(
            "SHIPUPI50",
            "customer",
            500.0,
            "test_user",
            payment_method="upi",
            shipping_charge=80.0,
            shipping_address=mock_address,
        )
        assert validation_upi["valid"] is True
        assert validation_upi["discount"] == 40.0  # 50% of 80.0 shipping

        # Test Case C: Validate percentage shipping discount with a different shipping charge
        validation_upi_diff = await coupon_repository.validateCoupon(
            "SHIPUPI50",
            "customer",
            500.0,
            "test_user",
            payment_method="upi",
            shipping_charge=40.0,
            shipping_address=mock_address,
        )
        assert validation_upi_diff["valid"] is True
        assert validation_upi_diff["discount"] == 20.0  # 50% of 40.0 shipping

        # Test Case D: Validate fixed shipping discount capping (100.0 discount value but 50.0 shipping charge)
        validation_fixed_capped = await coupon_repository.validateCoupon(
            "SHIPFIXED100",
            "customer",
            500.0,
            "test_user",
            payment_method="upi",
            shipping_charge=50.0,
            shipping_address=mock_address,
        )
        assert validation_fixed_capped["valid"] is True
        assert validation_fixed_capped["discount"] == 50.0  # Capped at shipping charge of 50.0

        # Test Case E: Validate fixed shipping discount undercap (100.0 discount value and 120.0 shipping charge)
        validation_fixed_undercap = await coupon_repository.validateCoupon(
            "SHIPFIXED100",
            "customer",
            500.0,
            "test_user",
            payment_method="upi",
            shipping_charge=120.0,
            shipping_address=mock_address,
        )
        assert validation_fixed_undercap["valid"] is True
        assert validation_fixed_undercap["discount"] == 100.0

    finally:
        # Cleanup
        await coupon_repository.storage.delete(ship_coupon["_id"])
        await coupon_repository.storage.delete(fixed_coupon["_id"])