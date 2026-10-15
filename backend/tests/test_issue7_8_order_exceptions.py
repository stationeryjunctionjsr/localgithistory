import pytest
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from app.services.order_service import create_order_service
from app.models.user import User
from app.models.schemas import Address


@pytest.mark.asyncio
async def test_issue7_delivery_slot_overbooking_raises_http_400():
    """Verify that when delivery slot increment fails (rowcount == 0),
    ValueError is NOT swallowed, the compensation block triggers,
    and HTTPException(status_code=400, detail='Delivery slot is fully booked or unavailable.') is raised."""

    mock_user = User(
        id=123,
        role="customer",
        name="Test Customer",
        phone="9999999999",
        is_active=True,
    )

    mock_order_data = MagicMock()
    mock_order_data.items = None
    mock_order_data.fulfillment_type = "hyperlocal"
    mock_order_data.delivery_slot_id = "slot_abc"
    mock_order_data.delivery_slot_date = "2026-10-16"
    mock_order_data.delivery_slot_config_id = "config_123"
    mock_order_data.is_urgent_delivery = False
    mock_order_data.payment_method = "cod"
    mock_order_data.coupon_code = None
    mock_order_data.referral_code = None
    mock_order_data.notes = ""
    address = Address(
        name="Test Customer",
        phone="9999999999",
        street="Main Road",
        address="123 Street",
        city="Jamshedpur",
        state="Jharkhand",
        district="East Singhbhum",
        pincode="831001",
        country="India",
    )
    mock_order_data.shipping_address = address
    mock_order_data.billing_address = address
    mock_order_data.seller_delivery_options = []

    mock_order = MagicMock()
    mock_order.id = "order_999"
    mock_order.order_number = "ORD-999"
    mock_order.created_at = "2026-10-16T10:00:00Z"
    mock_order.status = "pending"

    # Mock cart items
    mock_cart_item = MagicMock()
    mock_cart_item.product = 1
    mock_cart_item.quantity = 1
    mock_cart_item.price = 100.0
    mock_cart_item.variant_attributes = None
    mock_cart_item.bundle_id = None
    mock_cart_item.product_name = "Notebook"
    mock_cart_item.sell_as_case = False

    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Notebook"
    mock_product.price = 100.0
    mock_product.mrp = 120.0
    mock_product.stock = 10
    mock_product.category = "Stationery"
    mock_product.sku = "NOTE-1"
    mock_product.gst = 0
    mock_product.units_per_case = 1
    mock_product.case_qty = 1
    mock_product.is_active = True
    mock_product.product_type = "retail"
    mock_product.seller_id = "seller_1"
    mock_product.sellers = []

    # Setup database session mock where update_result.rowcount == 0 (overbooked)
    mock_session = AsyncMock()
    mock_update_result = MagicMock()
    mock_update_result.rowcount = 0
    mock_session.execute = AsyncMock(return_value=mock_update_result)
    mock_session.commit = AsyncMock()

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    mock_slot_cfg = MagicMock()
    mock_slot_cfg.id = "config_123"
    mock_slot_cfg.zoneDefaultCapacity = 10
    mock_slot = MagicMock()
    mock_slot.id = "slot_abc"
    mock_slot.isFullDay = False
    mock_slot.capacity = "10"
    mock_slot.booked_count = 5
    mock_slot.isUrgent = False
    mock_slot.cutoffHours = None
    mock_slot.urgentCutoffHours = None
    mock_slot_cfg.slots = [mock_slot]

    mock_slot_storage = MagicMock()
    mock_slot_storage.findAll = AsyncMock(return_value=[mock_slot_cfg])
    mock_slot_storage.findById = AsyncMock(return_value=mock_slot_cfg)
    mock_slot_storage.CHILD_TABLE = "sj_delivery_slots"
    mock_slot_storage.TABLE = "sj_delivery_slot_configs"

    with ExitStack() as stack:
        stack.enter_context(patch("app.repositories.order_repository.order_repository.storage.ensure_idempotency_index", new=AsyncMock()))
        stack.enter_context(patch("app.repositories.user_repository.user_repository.findById", new=AsyncMock(return_value=mock_user)))
        stack.enter_context(patch("app.repositories.order_repository.order_repository.countByUser", new=AsyncMock(return_value=1)))
        stack.enter_context(patch("app.repositories.coupon_repository.coupon_repository.get_active_automatic_product_discounts", new=AsyncMock(return_value=[])))
        stack.enter_context(patch("app.repositories.coupon_repository.coupon_repository.find_applicable_automatic_discounts", new=AsyncMock(return_value=[])))
        stack.enter_context(patch("app.repositories.feature_flag_repository.FeatureFlagRepository.is_enabled", new=AsyncMock(return_value=True)))
        stack.enter_context(patch("app.repositories.cart_repository.cart_repository.findByUser", new=AsyncMock(return_value=MagicMock(items=[mock_cart_item]))))
        stack.enter_context(patch("app.repositories.product_repository.product_repository.findByIds", new=AsyncMock(return_value=[mock_product])))
        stack.enter_context(patch("app.repositories.product_repository.product_repository.calculateTotalPrice", return_value=100.0))
        mock_zone = MagicMock()
        mock_zone.id = 1
        mock_zone.urgent_delivery_available = True
        stack.enter_context(patch("app.repositories.zone_seller_cache.get_zone_for_pincode", new=AsyncMock(return_value=mock_zone)))
        stack.enter_context(patch("app.repositories.zone_seller_cache.get_zone_id_and_seller_ids_for_pincode", new=AsyncMock(return_value=(1, ["seller_1"]))))
        stack.enter_context(patch("app.repositories.delivery_charge_repository.delivery_charge_repository.getHyperlocalChargeForZone", new=AsyncMock(return_value=MagicMock(charge=0.0))))
        stack.enter_context(patch("app.repositories.delivery_charge_repository.delivery_charge_repository.findAll", new=AsyncMock(return_value=[])))
        stack.enter_context(patch("app.repositories.delivery_charge_repository.delivery_charge_repository.getDefaultCharge", new=AsyncMock(return_value=None)))
        stack.enter_context(patch("app.repositories.product_repository.product_repository.findById", new=AsyncMock(return_value=mock_product)))
        stack.enter_context(patch("app.repositories.product_repository.product_repository.get_available_stock", new=AsyncMock(return_value=10)))
        stack.enter_context(patch("app.repositories.stock_reservation_repository.stock_reservation_repository.get_user_reservations", new=AsyncMock(return_value=[])))
        stack.enter_context(patch("app.repositories.order_repository.order_repository.generateOrderNumber", new=AsyncMock(return_value="ORD-999")))
        stack.enter_context(patch("app.repositories.order_repository.order_repository.storage.create_idempotent", new=AsyncMock(return_value=(mock_order, True))))
        mock_order_update = stack.enter_context(patch("app.repositories.order_repository.order_repository.update", new=AsyncMock()))
        stack.enter_context(patch("app.repositories.category_repository.category_repository.findByName", new=AsyncMock(return_value=None)))
        stack.enter_context(patch("app.config.database.get_async_session_factory", return_value=mock_factory))
        stack.enter_context(patch("app.db.storage_factory.get_storage", return_value=mock_slot_storage))

        with pytest.raises(HTTPException) as exc_info:
            await create_order_service(
                order_data=mock_order_data,
                current_user=mock_user,
                idempotency_key=None,
                background_tasks=MagicMock(),
            )

        assert exc_info.value.status_code == 400
        assert "Delivery slot is fully booked or unavailable." in exc_info.value.detail

        # Assert compensation ran: order status marked as "failed"
        mock_order_update.assert_called()
        call_args = mock_order_update.call_args[0]
        assert call_args[0] == "order_999"
        assert call_args[1].status == "failed"


@pytest.mark.asyncio
async def test_issue8_sub_order_failure_triggers_rollback_and_compensation():
    """Verify that when sub-order creation fails, the exception is NOT swallowed,
    the parent order is marked failed, and HTTPException(500) is raised."""

    mock_user = User(
        id=123,
        role="customer",
        name="Test Customer",
        phone="9999999999",
        is_active=True,
    )

    mock_order_data = MagicMock()
    mock_order_data.items = None
    mock_order_data.fulfillment_type = "hyperlocal"
    mock_order_data.delivery_slot_id = None
    mock_order_data.delivery_slot_date = None
    mock_order_data.delivery_slot_config_id = None
    mock_order_data.is_urgent_delivery = False
    mock_order_data.payment_method = "cod"
    mock_order_data.coupon_code = None
    mock_order_data.referral_code = None
    mock_order_data.notes = ""
    address2 = Address(
        name="Test Customer",
        phone="9999999999",
        street="Main Road",
        address="123 Street",
        city="Jamshedpur",
        state="Jharkhand",
        district="East Singhbhum",
        pincode="831001",
        country="India",
    )
    mock_order_data.shipping_address = address2
    mock_order_data.billing_address = address2
    mock_order_data.seller_delivery_options = []

    mock_order = MagicMock()
    mock_order.id = "order_1001"
    mock_order.order_number = "ORD-1001"
    mock_order.created_at = "2026-10-16T10:00:00Z"
    mock_order.status = "pending"

    mock_cart_item = MagicMock()
    mock_cart_item.product = 1
    mock_cart_item.quantity = 2
    mock_cart_item.price = 50.0
    mock_cart_item.variant_attributes = None
    mock_cart_item.bundle_id = None
    mock_cart_item.product_name = "Pen"
    mock_cart_item.sell_as_case = False

    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Pen"
    mock_product.price = 50.0
    mock_product.mrp = 60.0
    mock_product.stock = 20
    mock_product.category = "Stationery"
    mock_product.sku = "PEN-1"
    mock_product.gst = 0
    mock_product.units_per_case = 1
    mock_product.case_qty = 1
    mock_product.is_active = True
    mock_product.product_type = "retail"
    mock_product.seller_id = "seller_9"
    mock_product.sellers = []

    with ExitStack() as stack:
        stack.enter_context(patch("app.repositories.order_repository.order_repository.storage.ensure_idempotency_index", new=AsyncMock()))
        stack.enter_context(patch("app.repositories.user_repository.user_repository.findById", new=AsyncMock(return_value=mock_user)))
        stack.enter_context(patch("app.repositories.user_repository.user_repository.findSuperAdmin", new=AsyncMock(return_value=None)))
        stack.enter_context(patch("app.repositories.order_repository.order_repository.countByUser", new=AsyncMock(return_value=1)))
        stack.enter_context(patch("app.repositories.coupon_repository.coupon_repository.get_active_automatic_product_discounts", new=AsyncMock(return_value=[])))
        stack.enter_context(patch("app.repositories.coupon_repository.coupon_repository.find_applicable_automatic_discounts", new=AsyncMock(return_value=[])))
        stack.enter_context(patch("app.repositories.feature_flag_repository.FeatureFlagRepository.is_enabled", new=AsyncMock(return_value=True)))
        stack.enter_context(patch("app.repositories.cart_repository.cart_repository.findByUser", new=AsyncMock(return_value=MagicMock(items=[mock_cart_item]))))
        stack.enter_context(patch("app.repositories.product_repository.product_repository.findByIds", new=AsyncMock(return_value=[mock_product])))
        stack.enter_context(patch("app.repositories.product_repository.product_repository.calculateTotalPrice", return_value=100.0))
        mock_zone = MagicMock()
        mock_zone.id = 1
        mock_zone.urgent_delivery_available = True
        stack.enter_context(patch("app.repositories.zone_seller_cache.get_zone_for_pincode", new=AsyncMock(return_value=mock_zone)))
        stack.enter_context(patch("app.repositories.zone_seller_cache.get_zone_id_and_seller_ids_for_pincode", new=AsyncMock(return_value=(1, ["seller_1"]))))
        stack.enter_context(patch("app.repositories.delivery_charge_repository.delivery_charge_repository.getHyperlocalChargeForZone", new=AsyncMock(return_value=MagicMock(charge=0.0))))
        stack.enter_context(patch("app.repositories.delivery_charge_repository.delivery_charge_repository.findAll", new=AsyncMock(return_value=[])))
        stack.enter_context(patch("app.repositories.delivery_charge_repository.delivery_charge_repository.getDefaultCharge", new=AsyncMock(return_value=None)))
        stack.enter_context(patch("app.repositories.product_repository.product_repository.findById", new=AsyncMock(return_value=mock_product)))
        stack.enter_context(patch("app.repositories.product_repository.product_repository.get_available_stock", new=AsyncMock(return_value=10)))
        stack.enter_context(patch("app.repositories.product_repository.product_repository.decrement_stock_atomic", new=AsyncMock(return_value=18)))
        mock_restock = stack.enter_context(patch("app.repositories.product_repository.product_repository.increment_stock_atomic", new=AsyncMock()))
        stack.enter_context(patch("app.repositories.stock_reservation_repository.stock_reservation_repository.get_user_reservations", new=AsyncMock(return_value=[])))
        stack.enter_context(patch("app.repositories.stock_reservation_repository.stock_reservation_repository.fulfill_user_reservations", new=AsyncMock()))
        stack.enter_context(patch("app.repositories.stock_reservation_repository.stock_reservation_repository.release_user_reservations", new=AsyncMock()))
        stack.enter_context(patch("app.services.order_service.create_order_notification", new=AsyncMock()))
        stack.enter_context(patch("app.services.order_service.create_payment_notification", new=AsyncMock()))
        stack.enter_context(patch("app.repositories.payment_repository.payment_repository.create", new=AsyncMock(return_value=MagicMock(id=1))))
        stack.enter_context(patch("app.repositories.payment_repository.payment_repository.findByOrderId", new=AsyncMock(return_value=[])))
        stack.enter_context(patch("app.repositories.order_repository.order_repository.generateOrderNumber", new=AsyncMock(return_value="ORD-1001")))
        stack.enter_context(patch("app.repositories.order_repository.order_repository.storage.create_idempotent", new=AsyncMock(return_value=(mock_order, True))))
        mock_order_update = stack.enter_context(patch("app.repositories.order_repository.order_repository.update", new=AsyncMock()))
        stack.enter_context(patch("app.repositories.cart_repository.cart_repository.clearCart", new=AsyncMock()))
        stack.enter_context(patch("app.repositories.user_repository.user_repository.addSavedAddress", new=AsyncMock()))
        stack.enter_context(patch("app.repositories.user_repository.user_repository.update", new=AsyncMock()))
        stack.enter_context(patch("app.repositories.category_repository.category_repository.findByName", new=AsyncMock(return_value=None)))
        stack.enter_context(patch("app.repositories.sub_order_repository.sub_order_repository._generate_sub_order_number", return_value="SUB-1"))
        stack.enter_context(patch("app.repositories.sub_order_repository.sub_order_repository.create", side_effect=RuntimeError("Sub-order database constraint failure")))
        stack.enter_context(patch("app.services.order_service.populate_order", new=AsyncMock(return_value=MagicMock(user=mock_user))))

        with pytest.raises(HTTPException) as exc_info:
            await create_order_service(
                order_data=mock_order_data,
                current_user=mock_user,
                idempotency_key=None,
                background_tasks=MagicMock(),
            )

        assert exc_info.value.status_code == 500
        assert "sub-order allocation failure" in exc_info.value.detail.lower()

        # Verify parent order was marked failed instead of remaining valid
        mock_order_update.assert_called()
        call_args = mock_order_update.call_args[0]
        assert call_args[0] == "order_1001"
        assert call_args[1].status == "failed"

        # Verify stock was restored
        mock_restock.assert_called_with("1", 2)
