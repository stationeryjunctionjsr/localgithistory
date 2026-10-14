import ast
import inspect
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.valet_availability import ValetAvailability, EnrichedValetAvailability
from app.models.daos import (
    ValetAvailabilityFilter,
    ValetAvailabilityInternalCreate,
    ValetAvailabilityInternalUpdate,
)
from app.routers.valet_availability import (
    EnrichedValetAvailabilityResponse,
    ValetAvailabilityCreate,
)
from app.db.mysql_valet_availability_dao import MySQLValetAvailabilityDAO


def test_valet_availability_zero_lambdas_and_zero_build_where():
    import app.routers.valet_availability as router_mod
    import app.db.mysql_valet_availability_dao as dao_mod

    router_source = inspect.getsource(router_mod)
    dao_source = inspect.getsource(dao_mod)

    router_tree = ast.parse(router_source)
    dao_tree = ast.parse(dao_source)

    router_lambdas = [n for n in ast.walk(router_tree) if isinstance(n, ast.Lambda)]
    dao_lambdas = [n for n in ast.walk(dao_tree) if isinstance(n, ast.Lambda)]

    assert len(router_lambdas) == 0, f"Found lambdas in valet_availability router: {router_lambdas}"
    assert len(dao_lambdas) == 0, f"Found lambdas in mysql_valet_availability_dao: {dao_lambdas}"
    assert "_build_where" not in router_source
    assert "_build_where" not in dao_source


def test_valet_availability_zero_untyped_dicts_in_signatures():
    dao_methods = [
        MySQLValetAvailabilityDAO.findAll,
        MySQLValetAvailabilityDAO.findOne,
        MySQLValetAvailabilityDAO.findById,
        MySQLValetAvailabilityDAO.count,
        MySQLValetAvailabilityDAO.create,
        MySQLValetAvailabilityDAO.update,
        MySQLValetAvailabilityDAO.get_my_upcoming_availability,
        MySQLValetAvailabilityDAO.upsert_availability,
    ]
    for method in dao_methods:
        sig = inspect.signature(method)
        for param_name, param in sig.parameters.items():
            annotation = str(param.annotation)
            assert "dict" not in annotation.lower(), f"Untyped dict found in {method.__name__} parameter {param_name}: {annotation}"
            assert "any" not in annotation.lower(), f"Any found in {method.__name__} parameter {param_name}: {annotation}"


def test_valet_availability_filter_models():
    filt = ValetAvailabilityFilter(valet_id="v_101", date="2026-08-15")
    assert filt.valet_id == "v_101"
    assert filt.date == "2026-08-15"

    dumped = filt.model_dump(exclude_unset=True)
    assert dumped["valet_id"] == "v_101"
    assert dumped["date"] == "2026-08-15"


def test_valet_availability_models():
    now = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    model = ValetAvailability(
        id="10",
        valet_id="v_101",
        date="2026-08-15",
        availability_type="full_day",
        slots=[],
        zones=["zone_a", "zone_b"],
        created_at=now,
    )
    assert model.valet_id == "v_101"
    assert model.date == "2026-08-15"
    assert model.zones == ["zone_a", "zone_b"]

    data = model.model_dump(by_alias=True)
    assert data["valetId"] == "v_101"
    assert data["availabilityType"] == "full_day"


@pytest.mark.asyncio
async def test_dao_pushdown_async_execution():
    dao = MySQLValetAvailabilityDAO()
    mock_session = AsyncMock()
    mock_row = MagicMock()
    mock_row.id = 5
    mock_row.valet_id = "v_101"
    mock_row.date = "2026-08-15"
    mock_row.availability_type = "full_day"
    mock_row.created_at = datetime.now(timezone.utc)
    mock_row.updated_at = datetime.now(timezone.utc)

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]

    mock_slots_res = MagicMock()
    mock_slots_res.fetchall.return_value = []

    mock_zones_res = MagicMock()
    mock_zone_row = MagicMock()
    mock_zone_row.availability_id = 5
    mock_zone_row.zone = "zone_1"
    mock_zones_res.fetchall.return_value = [mock_zone_row]

    mock_session.execute.side_effect = [mock_result, mock_slots_res, mock_zones_res]

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_session_ctx.__aexit__.return_value = None
    mock_factory = MagicMock(return_value=mock_session_ctx)

    with patch("app.db.mysql_valet_availability_dao.get_async_session_factory", return_value=mock_factory):
        results = await dao.get_my_upcoming_availability("v_101", "2026-08-15", "2026-08-22")
        assert len(results) == 1
        assert results[0].valet_id == "v_101"
        assert results[0].zones == ["zone_1"]

        first_call_sql = str(mock_session.execute.call_args_list[0][0][0])
        assert "date >= :start_date" in first_call_sql
        assert "date <= :end_date" in first_call_sql
        assert "ORDER BY date ASC" in first_call_sql
