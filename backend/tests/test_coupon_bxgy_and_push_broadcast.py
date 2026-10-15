import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.repositories.coupon_repository import coupon_repository
from app.models.schemas import ItemSnippet, BxGyEvaluationResponse
from app.models.daos_flat import CouponInternal
from app.services.push_notification_service import PushNotificationService
from app.db.mysql_deviceSubscriptions_dao import MySQLDeviceSubscriptionsDAO


@pytest.mark.asyncio
async def test_calculate_bxgy_discount_pid_defined():
    coupon = MagicMock(spec=CouponInternal)
    coupon.applicable_item_type = "units"
    coupon.min_quantity_of_eligible_items = 2
    coupon.buy_x_get_y_customer_gets_quantity = 1
    coupon.applies_to_type = "all"
    coupon.applies_to_value_ids = None
    coupon.excluded_product_ids = None
    coupon.buy_x_get_y_customer_gets_applies_to_type = "all"
    coupon.bxgy_applies_to_ids = None
    coupon.bxgy_discount_type = "free"
    coupon.bxgy_discount_value = 0.0

    mock_p1 = MagicMock()
    mock_p1.id = 101
    mock_p1.quantity_per_case = 1

    mock_p2 = MagicMock()
    mock_p2.id = 102
    mock_p2.quantity_per_case = 1

    cart_items = [
        ItemSnippet(product_id=101, quantity=2, sell_as_case=False),
        ItemSnippet(product_id=102, quantity=1, sell_as_case=False),
    ]

    mock_product_repo = MagicMock()
    mock_product_repo.findByIds = AsyncMock(return_value=[mock_p1, mock_p2])
    mock_product_repo.calculateTotalPrice.side_effect = lambda prod, role, qty, **kwargs: 50.0 * qty if prod.id == 101 else 30.0 * qty

    with patch.object(coupon_repository, "_product_eligible_async", new=AsyncMock(return_value=True)), \
         patch.object(coupon_repository, "get_applicable_automatic_product_discounts", new=AsyncMock(return_value=[])):
        
        result = await coupon_repository._calculate_bxgy_discount(
            coupon=coupon,
            cart_items=cart_items,
            product_repository=mock_product_repo,
            user_role="customer",
            user_id="user_123"
        )

        assert isinstance(result, BxGyEvaluationResponse)
        assert result.discount > 0.0


@pytest.mark.asyncio
async def test_send_to_all_devices_sql_pushdown_broadcast():
    service = PushNotificationService()

    mock_notification = MagicMock()
    mock_notification.id = 1
    mock_notification.user_segment = "all"
    mock_notification.user_behavior = "none"
    mock_notification.scheduled_for = None
    mock_notification.title = "Test Notification"
    mock_notification.message = "Hello world"
    mock_notification.image = None
    mock_notification.link = "/shop"

    mock_reg_users = MagicMock()
    mock_reg_users.user_ids = {1, 2}
    mock_reg_users.has_guest = False

    mock_user1 = MagicMock()
    mock_user1.id = 1
    mock_user2 = MagicMock()
    mock_user2.id = 2

    mock_device1 = MagicMock()
    mock_device1.id = 10
    mock_device1.user_id = 1
    mock_device1.endpoint = None
    mock_device1.expo_token = "ExponentPushToken[xxxx]"

    mock_device2 = MagicMock()
    mock_device2.id = 11
    mock_device2.user_id = 2
    mock_device2.endpoint = None
    mock_device2.expo_token = "ExponentPushToken[yyyy]"

    mock_devices = [mock_device1, mock_device2]

    mock_find_all = AsyncMock(return_value=mock_devices)

    with patch("app.services.push_notification_service.push_notification_repository.device_storage.get_distinct_registered_user_ids", new=AsyncMock(return_value=mock_reg_users)), \
         patch("app.services.push_notification_service.push_notification_repository.device_storage.findAll", new=mock_find_all), \
         patch("app.services.push_notification_service.push_notification_repository.updateStats", new=AsyncMock(return_value=True)), \
         patch("app.services.push_notification_service.user_repository.findAll", new=AsyncMock(return_value=[mock_user1, mock_user2])), \
         patch("app.services.push_notification_service.order_repository.findAll", new=AsyncMock(return_value=[])), \
         patch.object(service, "_send_expo_push", return_value=2):

        # When segment is "all" and behavior is "none", it calls findAll() without user_ids filter
        res = await service.send_to_all_devices(mock_notification)
        assert res["totalDevices"] == 2
        assert res["deliveredCount"] == 2
        mock_find_all.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_send_to_all_devices_sql_pushdown_targeted():
    service = PushNotificationService()

    mock_notification = MagicMock()
    mock_notification.id = 2
    mock_notification.user_segment = "registered"
    mock_notification.user_behavior = "behavior1"
    mock_notification.scheduled_for = None
    mock_notification.title = "Targeted Notification"
    mock_notification.message = "Hello targeted"
    mock_notification.image = None
    mock_notification.link = "/shop"

    mock_reg_users = MagicMock()
    mock_reg_users.user_ids = {1}
    mock_reg_users.has_guest = True

    mock_user1 = MagicMock()
    mock_user1.id = 1

    mock_device1 = MagicMock()
    mock_device1.id = 10
    mock_device1.user_id = 1
    mock_device1.endpoint = None
    mock_device1.expo_token = "ExponentPushToken[xxxx]"

    mock_find_all = AsyncMock(return_value=[mock_device1])

    with patch("app.services.push_notification_service.push_notification_repository.device_storage.get_distinct_registered_user_ids", new=AsyncMock(return_value=mock_reg_users)), \
         patch("app.services.push_notification_service.push_notification_repository.device_storage.findAll", new=mock_find_all), \
         patch("app.services.push_notification_service.push_notification_repository.updateStats", new=AsyncMock(return_value=True)), \
         patch("app.services.push_notification_service.user_repository.findAll", new=AsyncMock(return_value=[mock_user1])), \
         patch("app.services.push_notification_service.order_repository.findAll", new=AsyncMock(return_value=[])), \
         patch.object(service, "is_user_targeted", new=AsyncMock(return_value=True)), \
         patch.object(service, "_send_expo_push", return_value=1):

        # Targeted: should pushdown user_ids={1} to findAll
        res = await service.send_to_all_devices(mock_notification)
        assert res["totalDevices"] == 1
        mock_find_all.assert_awaited_once_with(user_ids={1}, include_guests=False)


@pytest.mark.asyncio
async def test_device_dao_find_all_sql_pushdown():
    dao = MySQLDeviceSubscriptionsDAO()

    mock_session = AsyncMock()
    mock_exec = MagicMock()
    mock_exec.fetchall.return_value = []
    mock_session.execute.return_value = mock_exec

    with patch("app.db.mysql_deviceSubscriptions_dao.get_async_session_factory") as mock_factory:
        mock_factory.return_value.return_value.__aenter__.return_value = mock_session

        # 1. Query with user_ids and include_guests
        await dao.findAll(user_ids={101, 102}, include_guests=True)
        query = str(mock_session.execute.call_args_list[0][0][0])
        params = mock_session.execute.call_args_list[0][0][1]

        assert "user_id IN (:uid_0, :uid_1)" in query
        assert "user_id IS NULL" in query
        assert params["uid_0"] in (101, 102)
        assert params["uid_1"] in (101, 102)

        # 2. Query with empty user_ids and include_guests=False -> returns [] immediately without query
        mock_session.reset_mock()
        res = await dao.findAll(user_ids=set(), include_guests=False)
        assert res == []
        mock_session.execute.assert_not_called()
