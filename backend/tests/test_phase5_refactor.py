import ast
import inspect
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.tracking import ProductSearchCount, Tracking
from app.repositories.tracking_repository import TrackingRepository
import app.db.mysql_cart_dao as cart_dao_mod
import app.db.mysql_wishlist_dao as wishlist_dao_mod
import app.db.mysql_tracking_dao as tracking_dao_mod
import app.db.mysql_activities_dao as activities_dao_mod
import app.db.mysql_schemes_dao as schemes_dao_mod
import app.db.mysql_category_dao as category_dao_mod
import app.db.mysql_categoryTags_dao as category_tags_dao_mod
import app.db.mysql_division_dao as division_dao_mod
import app.db.mysql_saved_for_later_dao as saved_for_later_dao_mod
import app.repositories.tracking_repository as tracking_repo_mod


def _assert_no_defaultdict(module):
    source = inspect.getsource(module)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id != "defaultdict", f"Found defaultdict reference in {module.__name__} at line {node.lineno}"
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                assert alias.name != "defaultdict", f"Found defaultdict import in {module.__name__}"


def test_zero_defaultdict_in_all_phase5_modules():
    modules = [
        cart_dao_mod,
        wishlist_dao_mod,
        tracking_dao_mod,
        activities_dao_mod,
        schemes_dao_mod,
        category_dao_mod,
        category_tags_dao_mod,
        division_dao_mod,
        tracking_repo_mod,
    ]
    for mod in modules:
        _assert_no_defaultdict(mod)


def test_saved_for_later_dao_no_isinstance_in_to_ts():
    source = inspect.getsource(saved_for_later_dao_mod._to_ts)
    assert "isinstance" not in source, "Found isinstance in _to_ts"
    assert "type(val) is not str" in source, "Expected exact type check in _to_ts"


@pytest.mark.asyncio
async def test_tracking_repository_get_search_counts_returns_product_search_counts():
    repo = TrackingRepository()
    mock_doc1 = MagicMock(spec=Tracking)
    mock_doc1.product_ids = ["prod_1", "prod_2"]
    mock_doc2 = MagicMock(spec=Tracking)
    mock_doc2.product_ids = ["prod_1"]

    with patch.object(repo.storage, "find_by_date_range", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = [mock_doc1, mock_doc2]
        results = await repo.get_search_counts_by_product(days=7, segment="customer")

        assert isinstance(results, list)
        assert not isinstance(results, dict)
        assert len(results) == 2
        for r in results:
            assert isinstance(r, ProductSearchCount)

        result_by_id = {r.product_id: r.count for r in results}
        assert result_by_id["prod_1"] == 2
        assert result_by_id["prod_2"] == 1


@pytest.mark.asyncio
async def test_cart_dao_direct_row_hydration():
    from types import SimpleNamespace
    dao = cart_dao_mod.MySQLCartDAO()
    mock_cart_row = SimpleNamespace(
        id=1,
        user_id=42,
        created_at=None,
        updated_at=None,
    )

    mock_item_row = SimpleNamespace(
        id=10,
        cart_id=1,
        product_id="p100",
        quantity=3,
        sell_as_case=0,
        bundle_id=None,
        bundle_name=None,
        variant_attributes=None,
    )

    cart = dao._map_to_schema(mock_cart_row, [mock_item_row])
    assert cart.id == 1
    assert len(cart.items) == 1
    assert cart.items[0].product == "p100"
    assert cart.items[0].quantity == 3


@pytest.mark.asyncio
async def test_wishlist_dao_direct_row_hydration():
    from types import SimpleNamespace
    dao = wishlist_dao_mod.MySQLWishlistDAO()
    mock_wishlist_row = SimpleNamespace(
        id=5,
        user_id=99,
        created_at=None,
        updated_at=None,
    )

    mock_item = SimpleNamespace(
        wishlist_id=5,
        product_id=9,
    )

    w = dao._map_to_schema(mock_wishlist_row, [mock_item])
    assert w.id == 5
    assert len(w.items) == 1
    assert w.items[0].product == 9


def test_no_dict_unpacking_in_jobs_and_daos():
    """Verify no **dict unpacking exists in jobs, DAOs, repositories, or services."""
    import app.jobs.customer_segments_job as cs_job
    import app.jobs.events_sync_job as es_job
    import app.jobs.trending_job as tr_job
    import app.jobs.customer_favourites_job as cf_job
    import app.jobs.scheduled_notifications as sn_job
    import archive.flat_relational_dao as flat_dao
    import app.db.mysql_payment_dao as pay_dao
    import app.db.mysql_customer_segment_dao as cs_dao
    import app.repositories.analytics_repository as an_repo

    for mod in (cs_job, es_job, tr_job, cf_job, sn_job, flat_dao, pay_dao, cs_dao, an_repo):
        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    assert kw.arg is not None, f"Found **kwargs unpacking in {mod.__name__} at line {node.lineno}"
            elif isinstance(node, ast.Dict):
                for key in node.keys:
                    assert key is not None, f"Found **dict literal unpacking in {mod.__name__} at line {node.lineno}"


@pytest.mark.asyncio
async def test_session_dao_and_repo_targeted_dynamic_update():
    from app.db.mysql_session_dao import MySQLSessionDAO
    from app.repositories.session_repository import SessionRepository
    from app.models.daos import SessionInternalUpdate
    from app.models.session import Session

    dao = MySQLSessionDAO()

    # Mock DB session and execution
    executed_sqls = []
    executed_params = []

    mock_db_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()

    async def fake_execute(statement, params=None):
        executed_sqls.append(str(statement))
        executed_params.append(params or {})
        return mock_result

    mock_db_session.execute = fake_execute

    # Context manager mock for session factory
    class MockContextManager:
        async def __aenter__(self):
            return mock_db_session
        async def __aexit__(self, *args):
            pass

    dao._factory = MagicMock(return_value=lambda: MockContextManager())

    # Mock findById for post-update return
    fake_session = Session(id=123, status="revoked", revoked_reason="testing")
    dao.findById = AsyncMock(return_value=fake_session)

    # 1. Update only status and revoked_reason
    res = await dao.update(123, SessionInternalUpdate(status="revoked", revoked_reason="testing"))
    assert res is fake_session
    assert len(executed_sqls) == 1
    sql = executed_sqls[0]
    params = executed_params[0]

    # Verify SQL only targets provided fields
    assert "status = :status" in sql
    assert "revoked_reason = :revoked_reason" in sql
    assert "updated_at = :updated_at" in sql
    assert "user_id = :user_id" not in sql
    assert "refresh_token_id = :refresh_token_id" not in sql
    assert "comments = :comments" not in sql
    assert params["id"] == 123
    assert params["status"] == "revoked"
    assert params["revoked_reason"] == "testing"

    # 2. Test SessionRepository delegates directly without pre-read
    repo = SessionRepository()
    repo.storage = AsyncMock()
    repo.storage.update = AsyncMock(return_value=fake_session)

    update_payload = SessionInternalUpdate(refresh_token_id="new-token-123")
    repo_res = await repo.update_session(123, update_payload)
    assert repo_res is fake_session
    repo.storage.update.assert_awaited_once_with(123, update_payload)
    assert inspect.signature(MySQLSessionDAO.update).parameters["update_data"].annotation is SessionInternalUpdate
    assert inspect.signature(SessionRepository.update_session).parameters["updates"].annotation is SessionInternalUpdate


@pytest.mark.asyncio
async def test_banner_and_category_targeted_dynamic_updates():
    from datetime import datetime, timezone
    from app.db.mysql_banner_dao import MySQLBannerDAO
    from app.db.mysql_category_dao import MySQLCategoryDAO
    from app.models.daos import BannerInternalUpdate, CategoryInternalUpdate
    from app.models.schemas import BannerResponse
    from app.models.category import Category

    # 1. Verify MySQLBannerDAO targeted dynamic update
    banner_dao = MySQLBannerDAO()
    banner_sqls = []
    banner_params = []

    mock_db_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    mock_db_session.commit = AsyncMock()

    async def fake_banner_exec(statement, params=None):
        banner_sqls.append(str(statement))
        banner_params.append(params or {})
        return mock_result

    mock_db_session.execute = fake_banner_exec

    class MockContextManager:
        async def __aenter__(self):
            return mock_db_session
        async def __aexit__(self, *args):
            pass

    banner_dao._factory = MagicMock(return_value=lambda: MockContextManager())
    fake_banner = BannerResponse(
        id="50",
        title="Targeted Promo",
        displayOrder=5,
        imageUrl="https://img.com/promo.jpg",
        updatedAt=datetime.now(timezone.utc),
    )
    banner_dao.findById = AsyncMock(return_value=fake_banner)

    b_res = await banner_dao.update(50, BannerInternalUpdate(title="Targeted Promo", display_order=5))
    assert b_res is fake_banner
    assert len(banner_sqls) == 1
    b_sql = banner_sqls[0]
    b_p = banner_params[0]
    assert "title = :title" in b_sql
    assert "display_order = :display_order" in b_sql
    assert "description = :description" not in b_sql
    assert "image_url = :image_url" not in b_sql
    assert b_p["id"] == 50
    assert b_p["title"] == "Targeted Promo"
    assert b_p["display_order"] == 5

    # 2. Verify MySQLCategoryDAO targeted dynamic update
    category_dao = MySQLCategoryDAO()
    cat_sqls = []
    cat_params = []

    async def fake_cat_exec(statement, params=None):
        cat_sqls.append(str(statement))
        cat_params.append(params or {})
        return mock_result

    mock_cat_session = AsyncMock()
    mock_cat_session.execute = fake_cat_exec
    mock_cat_session.commit = AsyncMock()

    class MockCatContextManager:
        async def __aenter__(self):
            return mock_cat_session
        async def __aexit__(self, *args):
            pass

    category_dao._factory = MagicMock(return_value=lambda: MockCatContextManager())
    fake_cat = Category(id="99", name="Targeted Cat", is_active=True)
    category_dao.findById = AsyncMock(return_value=fake_cat)

    c_res = await category_dao.update(99, CategoryInternalUpdate(name="Targeted Cat", is_active=True))
    assert c_res is fake_cat
    assert len(cat_sqls) == 1
    c_sql = cat_sqls[0]
    c_p = cat_params[0]
    assert "name = :name" in c_sql
    assert "is_active = :is_active" in c_sql
    assert "description = :description" not in c_sql
    assert "minimum_quantity = :minimum_quantity" not in c_sql
    assert c_p["id"] == 99
    assert c_p["name"] == "Targeted Cat"
    assert c_p["is_active"] == 1


def test_category_and_banner_zero_anti_patterns():
    import app.repositories.category_repository as cat_repo_mod
    import app.db.mysql_category_dao as cat_dao_mod
    import app.routers.categories as cat_router_mod

    trees = {
        "cat_repo": ast.parse(inspect.getsource(cat_repo_mod)),
        "cat_dao": ast.parse(inspect.getsource(cat_dao_mod)),
        "cat_router": ast.parse(inspect.getsource(cat_router_mod)),
    }

    # Zero reflection calls (getattr, setattr, hasattr)
    for name, tree in trees.items():
        reflections = [
            n.func.id
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"getattr", "setattr", "hasattr"}
        ]
        assert len(reflections) == 0, f"Found reflection calls in {name}: {reflections}"

    # Verify no dual-ID branching (isdigit) or cid checks in category repository
    cat_repo_src = inspect.getsource(cat_repo_mod)
    assert "isdigit" not in cat_repo_src, "Found isdigit in CategoryRepository"
    assert "cid" not in cat_repo_src, "Found cid in CategoryRepository"
    assert "dict" not in cat_repo_src.lower(), "Found dict in CategoryRepository"

    # Verify category repo signatures use int
    sig_find = inspect.signature(cat_repo_mod.CategoryRepository.findById)
    assert sig_find.parameters["id"].annotation is int, f"findById expected int, got {sig_find.parameters['id'].annotation}"

    sig_update = inspect.signature(cat_repo_mod.CategoryRepository.update)
    assert sig_update.parameters["id"].annotation is int, f"update expected int, got {sig_update.parameters['id'].annotation}"

    sig_delete = inspect.signature(cat_repo_mod.CategoryRepository.delete)
    assert sig_delete.parameters["id"].annotation is int, f"delete expected int, got {sig_delete.parameters['id'].annotation}"

