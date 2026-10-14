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
    assert params["id"] == 42


def test_build_query_conditions_non_numeric_id():
    dao = MySQLOrderDAO()
    f = OrderFilter(id="non_numeric_123")
    where_sql, params = dao._build_query_conditions(f)
    assert "1=0" in where_sql


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
    assert params["u_int_0"] == 10
    assert params["u_int_1"] == 20


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
