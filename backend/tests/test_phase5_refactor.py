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

