import ast
import inspect
from typing import List, Optional
import pytest
from app.models.seller_availability import SellerAvailability
from app.models.daos_flat import (
    SellerAvailabilityFilter,
    SellerAvailabilityInternalCreate,
    SellerAvailabilityInternalUpdate,
)
from app.routers.seller_availability import (
    SellerAvailabilityItem,
    SellerAvailabilityResponse,
    _availability_sort_key,
)
from app.db.mysql_seller_availability_dao import MySQLSellerAvailabilityDAO


def test_seller_availability_zero_lambdas_and_zero_build_where():
    import app.routers.seller_availability as router_mod
    import app.db.mysql_seller_availability_dao as dao_mod

    router_source = inspect.getsource(router_mod)
    dao_source = inspect.getsource(dao_mod)

    router_tree = ast.parse(router_source)
    dao_tree = ast.parse(dao_source)

    router_lambdas = [n for n in ast.walk(router_tree) if isinstance(n, ast.Lambda)]
    dao_lambdas = [n for n in ast.walk(dao_tree) if isinstance(n, ast.Lambda)]

    assert len(router_lambdas) == 0, f"Found lambdas in seller_availability router: {router_lambdas}"
    assert len(dao_lambdas) == 0, f"Found lambdas in mysql_seller_availability_dao: {dao_lambdas}"
    assert "_build_where" not in router_source
    assert "_build_where" not in dao_source


def test_seller_availability_filter_models():
    filt = SellerAvailabilityFilter(seller_id="seller_123", statuses=["scheduled", "active"])
    assert filt.seller_id == "seller_123"
    assert filt.statuses == ["scheduled", "active"]

    dumped = filt.model_dump(exclude_unset=True)
    assert dumped["seller_id"] == "seller_123"
    assert dumped["statuses"] == ["scheduled", "active"]


def test_seller_availability_sort_key():
    item1 = SellerAvailabilityItem(startAt="2026-08-10T10:00:00Z", sellerId="s1")
    item2 = SellerAvailabilityItem(startAt="2026-08-12T10:00:00Z", sellerId="s2")
    item3 = SellerAvailabilityItem(startDate="2026-08-11T10:00:00Z", sellerId="s3")

    items = [item1, item2, item3]
    items.sort(key=_availability_sort_key, reverse=True)

    assert items[0].sellerId == "s2"
    assert items[1].sellerId == "s3"
    assert items[2].sellerId == "s1"


def test_seller_availability_model_properties():
    from datetime import datetime, timezone

    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    model = SellerAvailability(
        id="42",
        seller_id="seller_999",
        start_at=now,
        end_at=now,
        status="active",
    )
    assert model.sellerId == "seller_999"
    assert model.startAt == now.isoformat()
    assert model.endAt == now.isoformat()
    assert model.startDate == now.isoformat()
    assert model.endDate == now.isoformat()
