import ast
import inspect
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.daos import SellerRequestInternalCreate, SellerRequestInternalUpdate
from app.models.seller_request import SellerRequestResponseItem
import app.db.mysql_seller_request_dao as dao_mod
import app.routers.seller_requests as router_mod


def test_zero_anti_patterns_in_seller_request_dao():
    dao_source = inspect.getsource(dao_mod)
    tree = ast.parse(dao_source)

    # 1. Zero lambdas
    lambdas = [n for n in ast.walk(tree) if isinstance(n, ast.Lambda)]
    assert len(lambdas) == 0, f"Found lambdas: {lambdas}"

    # 2. Zero reflection calls (getattr, setattr, hasattr)
    reflection = [
        n.func.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"getattr", "setattr", "hasattr"}
    ]
    assert len(reflection) == 0, f"Found reflection calls: {reflection}"

    # 3. Zero isinstance checks
    isinstance_calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "isinstance"
    ]
    assert len(isinstance_calls) == 0, f"Found isinstance calls: {isinstance_calls}"

    # 4. Zero legacy alias shims
    assert not hasattr(dao_mod.MySQLSellerRequestDAO, "find_all")
    assert not hasattr(dao_mod.MySQLSellerRequestDAO, "find_by_id")
    assert not hasattr(dao_mod.MySQLSellerRequestDAO, "find_one")


def test_seller_request_internal_models_strictly_typed():
    # Verify responses field typing in internal models
    create_model = SellerRequestInternalCreate(
        user="test_user",
        responses=[
            SellerRequestResponseItem(
                admin_id="admin_1",
                response="Looking into it",
                created_at=datetime.now(timezone.utc),
            )
        ],
    )
    assert len(create_model.responses) == 1
    assert create_model.responses[0].admin_id == "admin_1"

    update_model = SellerRequestInternalUpdate(
        responses=[
            SellerRequestResponseItem(
                admin_id="admin_2",
                response="Resolved",
            )
        ]
    )
    assert len(update_model.responses) == 1
    assert update_model.responses[0].admin_id == "admin_2"


@pytest.mark.asyncio
async def test_mysql_seller_request_dao_delete_cascades_children():
    dao = dao_mod.MySQLSellerRequestDAO()
    mock_session = AsyncMock()
    mock_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session

    # Case 1: Numeric ID
    with patch.object(dao, "_factory", return_value=mock_factory):
        mock_session.execute.return_value = MagicMock(rowcount=1)
        res = await dao.delete(123)
        assert res is True

        # Verify SQL statements executed
        calls = [str(c[0][0]) for c in mock_session.execute.call_args_list]
        assert any("DELETE FROM sj_seller_request_attachments WHERE request_id = :rid" in c for c in calls)
        assert any("DELETE FROM sj_seller_request_responses WHERE request_id = :rid" in c for c in calls)
        assert any("DELETE FROM sj_seller_requests WHERE id = :rid" in c for c in calls)

    # Case 2: Invalid/falsy ID returns False directly
    res = await dao.delete(0)
    assert res is False


@pytest.mark.asyncio
async def test_mysql_seller_request_dao_replace_children_typed():
    dao = dao_mod.MySQLSellerRequestDAO()
    mock_session = AsyncMock()

    responses = [
        SellerRequestResponseItem(
            admin_id="adm_99",
            response="Thank you for contacting us",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    ]
    await dao._replace_children(
        mock_session,
        req_id=10,
        attachments=["https://example.com/file1.png"],
        responses=responses,
    )

    calls = [str(c[0][0]) for c in mock_session.execute.call_args_list]
    assert any("DELETE FROM sj_seller_request_attachments WHERE request_id = :rid" in c for c in calls)
    assert any("INSERT INTO sj_seller_request_attachments" in c for c in calls)
    assert any("DELETE FROM sj_seller_request_responses WHERE request_id = :rid" in c for c in calls)
    assert any("INSERT INTO sj_seller_request_responses" in c for c in calls)

    # Check insert params for response
    resp_insert_calls = [
        c[0][1] for c in mock_session.execute.call_args_list if "INSERT INTO sj_seller_request_responses" in str(c[0][0])
    ]
    assert len(resp_insert_calls) == 1
    assert resp_insert_calls[0]["admin"] == "adm_99"
    assert resp_insert_calls[0]["text"] == "Thank you for contacting us"
