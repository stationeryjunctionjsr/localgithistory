import ast
import inspect
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.seller_availability import SellerAvailability, SellerAvailabilityEnriched
from app.models.daos_flat import (
    SellerAvailabilityFilter,
    SellerAvailabilityInternalCreate,
    SellerAvailabilityInternalUpdate,
)
from app.routers.seller_availability import (
    SellerAvailabilityResponse,
    TickResponse,
)
from app.db.mysql_seller_availability_dao import MySQLSellerAvailabilityDAO


def test_zero_lambdas_and_zero_build_where():
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


def test_zero_untyped_dicts_in_signatures():
    dao_methods = [
        MySQLSellerAvailabilityDAO.findAll,
        MySQLSellerAvailabilityDAO.findOne,
        MySQLSellerAvailabilityDAO.count,
        MySQLSellerAvailabilityDAO.create,
        MySQLSellerAvailabilityDAO.update,
    ]
    for method in dao_methods:
        sig = inspect.signature(method)
        for param_name, param in sig.parameters.items():
            annotation = str(param.annotation)
            assert "dict" not in annotation.lower(), f"Untyped dict found in {method.__name__} parameter {param_name}: {annotation}"
            assert "any" not in annotation.lower(), f"Any found in {method.__name__} parameter {param_name}: {annotation}"


def test_seller_availability_filter_models():
    filt = SellerAvailabilityFilter(seller_id="seller_123", statuses=["scheduled", "active"])
    assert filt.seller_id == "seller_123"
    assert filt.statuses == ["scheduled", "active"]

    dumped = filt.model_dump(exclude_unset=True)
    assert dumped["seller_id"] == "seller_123"
    assert dumped["statuses"] == ["scheduled", "active"]


def test_seller_availability_models():
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    model = SellerAvailability(
        id="42",
        seller_id="seller_999",
        start_at=now,
        end_at=now,
        status="active",
    )
    assert model.seller_id == "seller_999"
    assert model.start_at == now
    assert model.end_at == now

    # Verify serialization to camelCase wire format
    data = model.model_dump(by_alias=True)
    assert data["sellerId"] == "seller_999"
    assert data["startAt"] == now


def test_dao_pushdown_queries_sql_generation():
    dao = MySQLSellerAvailabilityDAO()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    mock_result.fetchall.return_value = [("s1",), ("s2",)]
    mock_result.rowcount = 3
    mock_session.execute.return_value = mock_result
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_session_ctx.__aexit__.return_value = None
    mock_factory = MagicMock(return_value=mock_session_ctx)

    with patch.object(dao, "_get_session_factory", return_value=mock_factory):
        # 1. is_seller_currently_unavailable
        res_avail = pytest.run_async(dao.is_seller_currently_unavailable("s1")) if hasattr(pytest, "run_async") else None

    # Verify execute was called with pushdown SQL containing SELECT 1 and LIMIT 1
    # We test via direct async call:


@pytest.mark.asyncio
async def test_dao_pushdown_async_execution():
    dao = MySQLSellerAvailabilityDAO()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    from collections import namedtuple
    RowMock = namedtuple("RowMock", ["seller_id", "max_end_at"])
    mock_result.fetchall.return_value = [RowMock("seller_456", datetime(2026, 8, 17, 18, 0, 0, tzinfo=timezone.utc))]
    mock_result.rowcount = 2
    mock_session.execute.return_value = mock_result
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_session_ctx.__aexit__.return_value = None
    mock_factory = MagicMock(return_value=mock_session_ctx)

    with patch.object(dao, "_get_session_factory", return_value=mock_factory):
        is_unavail = await dao.is_seller_currently_unavailable("seller_456")
        assert is_unavail is True
        call_args = mock_session.execute.call_args[0]
        assert "SELECT 1 FROM" in str(call_args[0])
        assert "LIMIT 1" in str(call_args[0])

        zone_map = await dao.get_zone_unavailable_sellers_map({"seller_456"})
        assert "seller_456" in zone_map
        assert "2026-08-17" in zone_map["seller_456"]

        act, ended = await dao.advance_availability_statuses()
        assert act == 2
        assert ended == 2
