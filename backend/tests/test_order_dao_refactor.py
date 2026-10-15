import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.daos import OrderFilter
from app.db.mysql_order_dao import MySQLOrderDAO
from app.repositories.order_repository import OrderRepository


def test_order_filter_valid_fields():
    f = OrderFilter(
        id="123",
        user_id="user_abc",
        user_ids=["u1", "u2"],
        status="delivered",
        statuses=["pending_valet", "shipped"],
        order_type="retail",
        payment_method="cod",
        order_number_prefix="ORDER-RT-",
        idempotency_key="key_xyz",
        assigned_valet="valet_1",
        pending_valet_id="valet_2",
    )
    assert f.id == "123"
    assert f.user_id == "user_abc"
    assert f.user_ids == ["u1", "u2"]
    assert f.status == "delivered"
    assert f.statuses == ["pending_valet", "shipped"]
    assert f.order_type == "retail"
    assert f.payment_method == "cod"
    assert f.order_number_prefix == "ORDER-RT-"
    assert f.idempotency_key == "key_xyz"
    assert f.assigned_valet == "valet_1"
    assert f.pending_valet_id == "valet_2"


def test_order_filter_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        OrderFilter(legacy_unknown_field="not_allowed")


def test_order_filter_camel_case_input():
    # CamelBaseModel enables camelCase input aliases
    f = OrderFilter.model_validate({
        "userId": "u123",
        "orderNumberPrefix": "ORDER-",
        "idempotencyKey": "key1",
        "assignedValet": "v1",
        "pendingValetId": "v2",
    })
    assert f.user_id == "u123"
    assert f.order_number_prefix == "ORDER-"
    assert f.idempotency_key == "key1"
    assert f.assigned_valet == "v1"
    assert f.pending_valet_id == "v2"


def test_build_query_conditions_empty():
    dao = MySQLOrderDAO()
    where_sql, params = dao._build_query_conditions(None)
    assert where_sql == "1=1"
    assert params == {}


def test_build_query_conditions_numeric_id():
    dao = MySQLOrderDAO()
    f = OrderFilter(id="42")
    where_sql, params = dao._build_query_conditions(f)
    assert "id = :id" in where_sql
    assert params["id"] == "42"


def test_build_query_conditions_non_numeric_id():
    dao = MySQLOrderDAO()
    f = OrderFilter(id="non_numeric_123")
    where_sql, params = dao._build_query_conditions(f)
    assert "id = :id" in where_sql
    assert params["id"] == "non_numeric_123"


def test_build_query_conditions_statuses():
    dao = MySQLOrderDAO()
    f = OrderFilter(statuses=["pending_valet", "shipped", "return_pickup"])
    where_sql, params = dao._build_query_conditions(f)
    assert "status IN (:status_0, :status_1, :status_2)" in where_sql
    assert params["status_0"] == "pending_valet"
    assert params["status_1"] == "shipped"
    assert params["status_2"] == "return_pickup"


def test_build_query_conditions_user_ids():
    dao = MySQLOrderDAO()
    f = OrderFilter(user_ids=["10", "20"])
    where_sql, params = dao._build_query_conditions(f)
    assert "user_id IN (:u_int_0, :u_int_1)" in where_sql
    assert params["u_int_0"] == "10"
    assert params["u_int_1"] == "20"


@pytest.mark.asyncio
async def test_order_repository_delegates_filter():
    mock_storage = MagicMock()
    mock_storage.findAll = AsyncMock(return_value=[])
    mock_storage.count = AsyncMock(return_value=5)
    mock_storage.findByIds = AsyncMock(return_value=[])

    repo = OrderRepository()
    repo.storage = mock_storage

    f = OrderFilter(status="delivered")
    await repo.findAll(f, skip=0, limit=10)
    mock_storage.findAll.assert_called_once_with(f, skip=0, limit=10)

    cnt = await repo.count(f)
    assert cnt == 5
    mock_storage.count.assert_called_once_with(f)

    await repo.countByUser("user_42")
    # Verify count called with OrderFilter(user_id="user_42")
    call_args = mock_storage.count.call_args[0][0]
    assert isinstance(call_args, OrderFilter)
    assert call_args.user_id == "user_42"

    await repo.findByUser("user_42")
    call_args = mock_storage.findAll.call_args[0][0]
    assert isinstance(call_args, OrderFilter)
    assert call_args.user_id == "user_42"

    await repo.findByUser("user_42", status="delivered")
    call_args = mock_storage.findAll.call_args[0][0]
    assert isinstance(call_args, OrderFilter)
    assert call_args.user_id == "user_42"
    assert call_args.status == "delivered"

    await repo.findAll(user_id="user_99", status="pending")
    call_args = mock_storage.findAll.call_args[0][0]
    assert isinstance(call_args, OrderFilter)
    assert call_args.user_id == "user_99"
    assert call_args.status == "pending"

    await repo.findByIds(["1", "2"])
    mock_storage.findByIds.assert_called_once_with(["1", "2"])


def test_map_to_schema_direct_row_hydration():
    dao = MySQLOrderDAO()

    class FakeRow:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    order_row = FakeRow(
        id=10,
        user_id="1",
        order_number="ORDER-RT-1",
        status="delivered",
        total=150.0,
        subtotal=150.0,
        tax=0.0,
        shipping=0.0,
        discount=0.0,
        order_type="retail",
        payment_status="paid",
        payment_method="cod",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    item_rows = [
        FakeRow(order_id=10, product_id=1, quantity=2, price=50.0),
        FakeRow(order_id=20, product_id=2, quantity=1, price=100.0),
    ]
    decline_rows = [
        FakeRow(parent_id=10, valet_id="valet_a", reason="traffic"),
        FakeRow(parent_id=30, valet_id="valet_b", reason="distance"),
    ]

    mapped = dao._MySQLOrderDAO__map_to_schema(order_row, item_rows, decline_rows)
    assert mapped.id == 10
    assert len(mapped.items) == 1
    assert mapped.items[0].product_id == 1
    assert mapped.items[0].quantity == 2
    assert len(mapped.valet_decline_history) == 1
    assert mapped.valet_decline_history[0].valet_id == "valet_a"
    assert mapped.valet_decline_history[0].reason == "traffic"


@pytest.mark.asyncio
async def test_new_batch_sql_pushdown_dao_methods():
    dao = MySQLOrderDAO()

    class FakeRow:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch("app.db.mysql_order_dao.get_async_session_factory", return_value=mock_factory):
        # 1. get_sales_heatmap_stats
        mock_res1 = MagicMock()
        mock_res1.fetchall.return_value = [FakeRow(dow=0, hr=14, order_count=5, revenue=500.0)]
        mock_session.execute.return_value = mock_res1
        heatmap = await dao.get_sales_heatmap_stats()
        assert len(heatmap) == 1
        assert heatmap[0].dayOfWeek == "Monday"
        assert heatmap[0].hour == 14
        assert heatmap[0].orderCount == 5
        assert heatmap[0].revenue == 500.0

        # 2. get_net_sales_by_order_stats
        mock_res2 = MagicMock()
        mock_res2.fetchall.return_value = [
            FakeRow(
                order_id="1",
                order_number="ORD-1",
                customer_name="Alice",
                gross_sales=100.0,
                discount=10.0,
                tax=5.0,
                shipping=15.0,
                net_sales=110.0,
                status="delivered",
                created_at="2026-10-15 10:00:00",
            )
        ]
        mock_session.execute.return_value = mock_res2
        net_sales = await dao.get_net_sales_by_order_stats()
        assert len(net_sales) == 1
        assert net_sales[0].orderId == "1"
        assert net_sales[0].customerName == "Alice"
        assert net_sales[0].netSales == 110.0

        # 3. get_new_vs_returning_customer_stats
        mock_res3 = MagicMock()
        mock_res3.fetchall.return_value = [
            FakeRow(customer_type="New Customers", order_count=10, revenue=1000.0),
            FakeRow(customer_type="Returning Customers", order_count=20, revenue=3000.0),
        ]
        mock_session.execute.return_value = mock_res3
        new_vs_ret = await dao.get_new_vs_returning_customer_stats()
        assert len(new_vs_ret) == 2
        assert new_vs_ret[0].customerType == "New Customers"
        assert new_vs_ret[0].orderCount == 10
        assert new_vs_ret[1].customerType == "Returning Customers"
        assert new_vs_ret[1].revenue == 3000.0

        # 4. get_customer_frequency_stats
        mock_res4 = MagicMock()
        mock_res4.fetchall.return_value = [
            FakeRow(buyer_type="One-Time Buyers", customers=5, total_orders=5, total_revenue=500.0),
            FakeRow(buyer_type="Repeat Buyers", customers=5, total_orders=15, total_revenue=2000.0),
        ]
        mock_session.execute.return_value = mock_res4
        freq = await dao.get_customer_frequency_stats()
        assert len(freq) == 2
        assert freq[0].type == "One-Time Buyers"
        assert freq[0].customers == 5
        assert freq[0].customerPct == 50.0
        assert freq[1].type == "Repeat Buyers"
        assert freq[1].avgOrders == 3.0

        # 5. get_rfm_segments_stats
        mock_res5 = MagicMock()
        mock_res5.fetchall.return_value = [
            FakeRow(
                user_id="u1",
                name="Bob",
                email="bob@example.com",
                order_count=6,
                total_spend=1500.0,
                recency_days=10,
                last_order="2026-10-10",
            )
        ]
        mock_session.execute.return_value = mock_res5
        rfm = await dao.get_rfm_segments_stats()
        assert len(rfm) == 1
        assert rfm[0].userId == "u1"
        assert rfm[0].segment == "Champion"
        assert rfm[0].recencyDays == 10
        assert rfm[0].orderCount == 6


@pytest.mark.asyncio
async def test_batch_3_sql_pushdown_dao_methods():
    dao = MySQLOrderDAO()

    class FakeRow:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch("app.db.mysql_order_dao.get_async_session_factory", return_value=mock_factory):
        # 1. get_discounts_audit_stats
        mock_res1 = MagicMock()
        mock_res1.fetchall.return_value = [
            FakeRow(
                order_id="101",
                order_number="ORD-101",
                created_at="2026-10-15 12:00:00",
                customer_name="Resham",
                gross_sales=200.0,
                discount_applied=20.0,
                discount_pct=10.0,
                couponCode="DISC10",
                coupon_code="DISC10",
                net_after_discount=180.0,
            )
        ]
        mock_session.execute.return_value = mock_res1
        discounts = await dao.get_discounts_audit_stats()
        assert len(discounts) == 1
        assert discounts[0].orderId == "101"
        assert discounts[0].customerName == "Resham"
        assert discounts[0].netAfterDiscount == 180.0

        # 2. get_sales_by_channel_detailed_stats
        mock_res2 = MagicMock()
        mock_res2.fetchall.return_value = [
            FakeRow(channel="desktop_web", order_count=10, revenue=5000.0),
            FakeRow(channel="mobile_app", order_count=5, revenue=2500.0),
        ]
        mock_session.execute.return_value = mock_res2
        channels = await dao.get_sales_by_channel_detailed_stats()
        assert len(channels) == 2
        assert channels[0].channel == "desktop_web"
        assert channels[0].channelLabel == "Desktop Web"
        assert channels[0].orderCount == 10
        assert channels[0].revenue == 5000.0
        assert channels[0].revenuePct == 66.7

        # 3. get_items_bought_together_stats
        mock_res3 = MagicMock()
        mock_res3.fetchall.return_value = [
            FakeRow(
                product_a_id="p1",
                product_a_name="Notebook",
                product_b_id="p2",
                product_b_name="Pen",
                frequency=12,
            )
        ]
        mock_session.execute.return_value = mock_res3
        pairs = await dao.get_items_bought_together_stats(limit=5)
        assert len(pairs) == 1
        assert pairs[0].productAId == "p1"
        assert pairs[0].productBId == "p2"
        assert pairs[0].frequency == 12

        # 4. get_sales_by_device_type_stats
        mock_res4 = MagicMock()
        mock_res4.fetchall.return_value = [
            FakeRow(device_type="mobile", order_count=8, revenue=1200.0)
        ]
        mock_session.execute.return_value = mock_res4
        devices = await dao.get_sales_by_device_type_stats()
        assert len(devices) == 1
        assert devices[0].deviceType == "mobile"
        assert devices[0].orderCount == 8
        assert devices[0].revenue == 1200.0

        # 5. get_products_pct_sold_stats
        mock_res5 = MagicMock()
        mock_res5.fetchall.return_value = [
            FakeRow(
                product_id="p1",
                name="Notebook",
                sku="NB-01",
                category="Stationery",
                opening_stock=100,
                current_stock=80,
                units_sold=20,
                pct_sold=20.0,
            )
        ]
        mock_session.execute.return_value = mock_res5
        pct_sold = await dao.get_products_pct_sold_stats()
        assert len(pct_sold) == 1
        assert pct_sold[0].productId == "p1"
        assert pct_sold[0].unitsSold == 20
        assert pct_sold[0].pctSold == 20.0


@pytest.mark.asyncio
async def test_pushdown_analytics_batch4():
    dao = MySQLOrderDAO()

    class FakeRow:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    mock_session = AsyncMock()
    mock_ctx = MagicMock()
    mock_ctx.__aenter__.return_value = mock_session
    mock_ctx.__aexit__.return_value = None
    mock_factory = MagicMock(return_value=mock_ctx)

    with patch("app.db.mysql_order_dao.get_async_session_factory", return_value=mock_factory):
        # 1. get_inventory_runway_stats
        mock_res1 = MagicMock()
        mock_res1.fetchall.return_value = [
            FakeRow(
                product_id="p1",
                name="Notebook",
                category="Stationery",
                current_stock=60,
                units_sold_30d=30,
                avg_daily_sales=1.0,
                days_remaining=60.0,
            )
        ]
        mock_session.execute.return_value = mock_res1
        runway = await dao.get_inventory_runway_stats()
        assert len(runway) == 1
        assert runway[0].productId == "p1"
        assert runway[0].name == "Notebook"
        assert runway[0].category == "Stationery"
        assert runway[0].currentStock == 60
        assert runway[0].unitsSold30d == 30
        assert runway[0].avgDailySales == 1.0
        assert runway[0].daysRemaining == 60.0

        # 2. get_bundle_performance_report_stats
        mock_res2 = MagicMock()
        mock_res2.fetchall.return_value = [
            FakeRow(
                bundle_id="b1",
                name="Starter Pack",
                status="active",
                is_active=True,
                price=99.99,
                copies_sold=15,
                order_count=15,
                revenue=1499.85,
            )
        ]
        mock_session.execute.return_value = mock_res2
        bundles = await dao.get_bundle_performance_report_stats()
        assert len(bundles) == 1
        assert bundles[0].bundleId == "b1"
        assert bundles[0].name == "Starter Pack"
        assert bundles[0].status == "active"
        assert bundles[0].isActive is True
        assert bundles[0].price == 99.99
        assert bundles[0].copiesSold == 15
        assert bundles[0].orderCount == 15
        assert bundles[0].revenue == 1499.85
        assert bundles[0].monthlyRevenue == []

        # 3. get_returns_report_stats
        mock_res3 = MagicMock()
        mock_res3.fetchall.return_value = [
            FakeRow(
                return_id="RET-001",
                order_id=101,
                created_at=datetime(2026, 10, 15, 10, 0, 0),
                status="approved",
                refund_value=150.0,
                user_name="John Doe",
                user_email="john@example.com",
                item_count=2,
                payment_method="card",
                order_total=300.0,
            )
        ]
        mock_session.execute.return_value = mock_res3
        returns = await dao.get_returns_report_stats()
        assert len(returns) == 1
        assert returns[0].returnId == "RET-001"
        assert returns[0].orderId == 101
        assert returns[0].createdAt == datetime(2026, 10, 15, 10, 0, 0)
        assert returns[0].status == "approved"
        assert returns[0].refundValue == 150.0
        assert returns[0].userName == "John Doe"
        assert returns[0].userEmail == "john@example.com"
        assert returns[0].itemCount == 2
        assert returns[0].paymentMethod == "card"
        assert returns[0].orderTotal == 300.0

        # 4. get_top_returned_products_stats
        mock_res4 = MagicMock()
        mock_res4.fetchall.return_value = [
            FakeRow(
                product_id="p1",
                product_name="Notebook",
                category="Stationery",
                return_count=5,
                quantity_returned=10,
                revenue_lost=250.0,
            )
        ]
        mock_session.execute.return_value = mock_res4
        top_returned = await dao.get_top_returned_products_stats(limit=10)
        assert len(top_returned) == 1
        assert top_returned[0].productId == "p1"
        assert top_returned[0].productName == "Notebook"
        assert top_returned[0].category == "Stationery"
        assert top_returned[0].returnCount == 5
        assert top_returned[0].quantityReturned == 10
        assert top_returned[0].revenueLost == 250.0

        # 5. get_inventory_value_by_category_stats
        mock_res5 = MagicMock()
        mock_res5.fetchall.return_value = [
            FakeRow(
                category="Electronics",
                product_count=10,
                total_stock=500,
                inventory_value=25000.0,
            )
        ]
        mock_session.execute.return_value = mock_res5
        cat_values = await dao.get_inventory_value_by_category_stats()
        assert len(cat_values) == 1
        assert cat_values[0].category == "Electronics"
        assert cat_values[0].productCount == 10
        assert cat_values[0].totalStock == 500
        assert cat_values[0].inventoryValue == 25000.0

        # 6. get_inventory_alerts_stats
        mock_res6 = MagicMock()
        mock_res6.fetchall.return_value = [
            FakeRow(
                product_id=1,
                name="Notebook",
                sku="NB-01",
                category="Stationery",
                stock=2,
                status="low_stock",
            )
        ]
        mock_session.execute.return_value = mock_res6
        alerts = await dao.get_inventory_alerts_stats(threshold=5)
        assert len(alerts) == 1
        assert alerts[0].productId == 1
        assert alerts[0].name == "Notebook"
        assert alerts[0].sku == "NB-01"
        assert alerts[0].category == "Stationery"
        assert alerts[0].stock == 2
        assert alerts[0].status == "low_stock"


@pytest.mark.asyncio
async def test_analytics_repository_batch_7_delegation():
    from app.repositories.analytics_repository import analytics_repository
    from app.models.analytics_schemas import (
        RFMSegmentsResponse,
        CustomerFrequencyResponse,
        NetSalesResponse,
        SalesHeatmapResponse,
        InventoryRunwayResponse,
        SalesByChannelDetailedResponse,
        DiscountsAuditResponse,
        ProductsPctSoldResponse,
    )

    mock_rfm = [RFMSegmentsResponse(userId="1", name="Alice", email="alice@test.com", segment="Champion", recencyDays=5, orderCount=10, totalSpend=500.0)]
    mock_freq = [CustomerFrequencyResponse(type="One-Time Buyers", customers=1, customerPct=100.0, orders=1, avgOrders=1.0, revenue=50.0)]
    mock_net = [NetSalesResponse(orderId=1, orderNumber="ORD-1", customerName="Alice", grossSales=100.0, discount=10.0, tax=5.0, shipping=5.0, netSales=100.0, status="delivered", createdAt="2026-03-15T10:00:00")]
    mock_heat = [SalesHeatmapResponse(dayOfWeek="Monday", hour=10, orderCount=2, revenue=200.0)]
    mock_runway = [InventoryRunwayResponse(productId=1, name="Notebook", category="Stationery", currentStock=50, unitsSold30d=10, avgDailySales=0.33, daysRemaining=151.0)]
    mock_chan = [SalesByChannelDetailedResponse(channel="desktop_web", channelLabel="Desktop Web", orderCount=5, revenue=500.0, aov=100.0, revenuePct=100.0)]
    mock_disc = [DiscountsAuditResponse(orderId=1, orderNumber="ORD-1", customerName="Alice", couponCode="SAVE10", discountType="percentage", discountValue=10.0, grossSales=100.0, discountApplied=10.0, netAfterDiscount=90.0, discountPct=10.0, createdAt="2026-03-15T10:00:00")]
    mock_pct = [ProductsPctSoldResponse(productId=1, name="Notebook", category="Stationery", sku="NB-1", unitsSold=5, currentStock=20, openingStock=25, pctSold=20.0)]

    with patch.object(analytics_repository.order_storage, "get_rfm_segments_stats", new_callable=AsyncMock, return_value=mock_rfm) as m_rfm, \
         patch.object(analytics_repository.order_storage, "get_customer_frequency_stats", new_callable=AsyncMock, return_value=mock_freq) as m_freq, \
         patch.object(analytics_repository.order_storage, "get_net_sales_by_order_stats", new_callable=AsyncMock, return_value=mock_net) as m_net, \
         patch.object(analytics_repository.order_storage, "get_sales_heatmap_stats", new_callable=AsyncMock, return_value=mock_heat) as m_heat, \
         patch.object(analytics_repository.order_storage, "get_inventory_runway_stats", new_callable=AsyncMock, return_value=mock_runway) as m_runway, \
         patch.object(analytics_repository.order_storage, "get_sales_by_channel_detailed_stats", new_callable=AsyncMock, return_value=mock_chan) as m_chan, \
         patch.object(analytics_repository.order_storage, "get_discounts_audit_stats", new_callable=AsyncMock, return_value=mock_disc) as m_disc, \
         patch.object(analytics_repository.order_storage, "get_products_pct_sold_stats", new_callable=AsyncMock, return_value=mock_pct) as m_pct:

        res_rfm = await analytics_repository.get_rfm_segments(seller_id=10)
        assert res_rfm == mock_rfm
        m_rfm.assert_awaited_once_with(start_date=None, end_date=None, seller_id=10)

        res_freq = await analytics_repository.get_customer_frequency_report(seller_id=10)
        assert res_freq == mock_freq
        m_freq.assert_awaited_once_with(start_date=None, end_date=None, seller_id=10)

        res_net = await analytics_repository.get_net_sales_by_order(seller_id=10)
        assert res_net == mock_net
        m_net.assert_awaited_once_with(start_date=None, end_date=None, seller_id=10)

        res_heat = await analytics_repository.get_sales_heatmap(seller_id=10)
        assert res_heat == mock_heat
        m_heat.assert_awaited_once_with(start_date=None, end_date=None, seller_id=10)

        res_runway = await analytics_repository.get_inventory_runway(seller_id=10)
        assert res_runway == mock_runway
        m_runway.assert_awaited_once_with(start_date=None, end_date=None, seller_id=10)

        res_chan = await analytics_repository.get_sales_by_channel_detailed()
        assert res_chan == mock_chan
        m_chan.assert_awaited_once_with(start_date=None, end_date=None)

        res_disc = await analytics_repository.get_discounts_audit(seller_id=10)
        assert res_disc == mock_disc
        m_disc.assert_awaited_once_with(start_date=None, end_date=None, seller_id=10)

        res_pct = await analytics_repository.get_products_pct_sold(seller_id=10)
        assert res_pct == mock_pct
        m_pct.assert_awaited_once_with(start_date=None, end_date=None, seller_id=10)





