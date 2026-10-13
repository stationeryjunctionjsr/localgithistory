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


@pytest.mark.asyncio
async def test_five_new_daos_targeted_dynamic_updates_and_zero_dict():
    import app.db.mysql_brand_dao as brand_dao_mod
    import app.db.mysql_feature_flag_dao as ff_dao_mod
    import app.db.mysql_commission_settings_dao as comm_dao_mod
    import app.db.mysql_faq_section_dao as faq_dao_mod
    import app.db.mysql_division_dao as div_dao_mod
    import app.repositories.brand_repository as brand_repo_mod
    import app.repositories.feature_flag_repository as ff_repo_mod
    import app.repositories.division_repository as div_repo_mod

    from app.models.daos import BrandInternalUpdate
    from app.models.feature_flag import FeatureFlagUpdate
    from app.models.commission_settings import CommissionSettingsInternalUpdate
    from app.models.faq_section import FaqSectionInternalUpdate
    from app.models.division import DivisionInternalUpdate

    # 1. AST Check: Zero reflection calls and zero dict in repo/dao signatures
    modules_to_check = [
        brand_dao_mod, ff_dao_mod, comm_dao_mod, faq_dao_mod, div_dao_mod,
        brand_repo_mod, ff_repo_mod, div_repo_mod
    ]
    for mod in modules_to_check:
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"getattr", "setattr", "hasattr"}:
                assert False, f"Found reflection call {node.func.id} in {mod.__name__}"
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    if arg.annotation and isinstance(arg.annotation, ast.Name):
                        assert arg.annotation.id not in {"dict", "Dict"}, f"Found dict/Dict parameter in {mod.__name__}.{node.name}"

    import app.routers.feature_flags as ff_router_mod
    assert "isdigit" not in inspect.getsource(ff_router_mod), "Found isdigit in feature_flags router"
    assert "isdigit" not in inspect.getsource(ff_repo_mod), "Found isdigit in feature_flags repository"
    assert "isdigit" not in inspect.getsource(ff_dao_mod), "Found isdigit in feature_flags DAO"

    # Helper for DB mock
    def setup_mock_db():
        executed = []
        mock_session = AsyncMock()
        mock_res = MagicMock()
        mock_res.rowcount = 1

        async def fake_exec(stmt, p=None):
            executed.append((str(stmt), p or {}))
            return mock_res

        mock_session.execute = fake_exec
        mock_session.commit = AsyncMock()

        class MockCtx:
            async def __aenter__(self):
                return mock_session
            async def __aexit__(self, *args):
                pass

        return executed, lambda: MockCtx()

    # 2. Test MySQLBrandDAO dynamic update
    b_dao = brand_dao_mod.MySQLBrandDAO()
    b_exec, b_factory = setup_mock_db()
    b_dao._factory = MagicMock(return_value=b_factory)
    b_dao.findById = AsyncMock(return_value=MagicMock())
    await b_dao.update(10, BrandInternalUpdate(name="Acme Corp"))
    assert len(b_exec) == 1
    sql, params = b_exec[0]
    assert "name = :name" in sql
    assert "slug = :slug" in sql
    assert "image_url = :image_url" not in sql
    assert "show_in_mobile_homepage = :show_in_mobile_homepage" not in sql
    assert params["id"] == 10
    assert params["name"] == "Acme Corp"
    assert params["slug"] == "acme-corp"

    # 3. Test MySQLFeatureFlagDAO dynamic update
    ff_dao = ff_dao_mod.MySQLFeatureFlagDAO()
    ff_exec, ff_factory = setup_mock_db()
    ff_dao._factory = MagicMock(return_value=ff_factory)
    ff_dao.findById = AsyncMock(return_value=MagicMock())
    await ff_dao.update(20, FeatureFlagUpdate(enabled=True))
    assert len(ff_exec) == 1
    sql, params = ff_exec[0]
    assert "enabled = :enabled" in sql
    assert "name = :name" not in sql
    assert "category = :category" not in sql
    assert params["id"] == 20
    assert params["enabled"] == 1

    # 4. Test MySQLCommissionSettingsDAO dynamic update
    c_dao = comm_dao_mod.MySQLCommissionSettingsDAO()
    c_exec, c_factory = setup_mock_db()
    c_dao._factory = MagicMock(return_value=c_factory)
    c_dao.findById = AsyncMock(return_value=MagicMock())
    await c_dao.update(30, CommissionSettingsInternalUpdate(default_commission_pct=12.5))
    assert len(c_exec) == 1
    sql, params = c_exec[0]
    assert "default_commission_pct = :pct" in sql
    assert params["id"] == 30
    assert params["pct"] == 12.5

    # 5. Test MySQLFaqSectionDAO dynamic update
    faq_dao = faq_dao_mod.MySQLFaqSectionDAO()
    faq_exec, faq_factory = setup_mock_db()
    with patch("app.db.mysql_faq_section_dao.get_async_session_factory", return_value=faq_factory):
        faq_dao.findById = AsyncMock(return_value=MagicMock())
        await faq_dao.update(40, FaqSectionInternalUpdate(title="Billing FAQ"))
        assert len(faq_exec) == 1
        sql, params = faq_exec[0]
        assert "title = :title" in sql
        assert "order_index = :oi" not in sql
        assert "is_active = :ia" not in sql
        assert params["id"] == 40
        assert params["title"] == "Billing FAQ"

    # 6. Test MySQLDivisionDAO dynamic update
    div_dao = div_dao_mod.MySQLDivisionDAO()
    div_exec, div_factory = setup_mock_db()
    div_dao._factory = MagicMock(return_value=div_factory)
    div_dao.findById = AsyncMock(return_value=MagicMock())
    await div_dao.update(50, DivisionInternalUpdate(name="Electronics Division", is_active=True))
    assert len(div_exec) == 1
    sql, params = div_exec[0]
    assert "name = :name" in sql
    assert "is_active = :act" in sql
    assert "description = :desc" not in sql
    assert "image_url = :img" not in sql
    assert params["id"] == 50
    assert params["name"] == "Electronics Division"
    assert params["act"] == 1


@pytest.mark.asyncio
async def test_four_more_daos_targeted_dynamic_updates_and_zero_dict():
    import app.db.mysql_ad_dao as ad_dao_mod
    import app.db.mysql_categoryTags_dao as cat_tags_dao_mod
    import app.db.mysql_schemes_dao as schemes_dao_mod
    import app.db.mysql_searchTags_dao as search_tags_dao_mod
    import app.routers.ads as ads_router_mod
    import app.repositories.search_tag_repository as search_tag_repo_mod

    from app.models.schemas import AdUpdate
    from app.models.daos_flat import CategoryTagInternalUpdate, SchemeInternalUpdate, SearchTagInternalUpdate

    # 1. AST Check: Zero reflection calls, zero dict in signatures, zero isdigit
    modules_to_check = [
        ad_dao_mod, cat_tags_dao_mod, schemes_dao_mod, search_tags_dao_mod,
        ads_router_mod, search_tag_repo_mod
    ]
    for mod in modules_to_check:
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"getattr", "setattr", "hasattr"}:
                assert False, f"Found reflection call {node.func.id} in {mod.__name__}"
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    if arg.annotation and isinstance(arg.annotation, ast.Name):
                        assert arg.annotation.id not in {"dict", "Dict"}, f"Found dict/Dict parameter in {mod.__name__}.{node.name}"

    assert "isdigit" not in inspect.getsource(ads_router_mod), "Found isdigit in ads router"
    assert "isdigit" not in inspect.getsource(ad_dao_mod), "Found isdigit in ad DAO"
    assert "isdigit" not in inspect.getsource(cat_tags_dao_mod), "Found isdigit in categoryTags DAO"
    assert "isdigit" not in inspect.getsource(schemes_dao_mod), "Found isdigit in schemes DAO"
    assert "isdigit" not in inspect.getsource(search_tags_dao_mod), "Found isdigit in searchTags DAO"

    # Helper for DB mock
    def setup_mock_db():
        executed = []
        mock_session = AsyncMock()
        mock_res = MagicMock()
        mock_res.rowcount = 1

        async def fake_exec(stmt, p=None):
            executed.append((str(stmt), p or {}))
            return mock_res

        mock_session.execute = fake_exec
        mock_session.commit = AsyncMock()

        class MockCtx:
            async def __aenter__(self):
                return mock_session
            async def __aexit__(self, *args):
                pass

        return executed, lambda: MockCtx()

    # 2. Test MySQLAdDAO targeted dynamic update
    ad_dao = ad_dao_mod.MySQLAdDAO()
    ad_exec, ad_factory = setup_mock_db()
    ad_dao._factory = MagicMock(return_value=ad_factory)
    ad_dao.findById = AsyncMock(return_value=MagicMock())
    await ad_dao.update(101, AdUpdate(name="Flash Sale", status="active"))
    assert len(ad_exec) == 1
    sql, params = ad_exec[0]
    assert "name = :name" in sql
    assert "status = :status" in sql
    assert "headline = :headline" not in sql
    assert "image_url = :image_url" not in sql
    assert params["id"] == 101
    assert params["name"] == "Flash Sale"
    assert params["status"] == "active"

    # 3. Test MySQLCategoryTagsDAO targeted dynamic update
    ct_dao = cat_tags_dao_mod.MySQLCategoryTagsDAO()
    ct_exec, ct_factory = setup_mock_db()
    ct_dao._factory = MagicMock(return_value=ct_factory)
    ct_dao.findById = AsyncMock(return_value=MagicMock())
    await ct_dao.update(202, CategoryTagInternalUpdate(name="Trending Tag"))
    assert len(ct_exec) == 1
    sql, params = ct_exec[0]
    assert "name = :name" in sql
    assert "description = :desc" not in sql
    assert "is_active = :act" not in sql
    assert params["id"] == 202
    assert params["name"] == "Trending Tag"

    # 4. Test MySQLSchemesDAO targeted dynamic update
    sc_dao = schemes_dao_mod.MySQLSchemesDAO()
    sc_exec, sc_factory = setup_mock_db()
    sc_dao._factory = MagicMock(return_value=sc_factory)
    sc_dao.findById = AsyncMock(return_value=MagicMock())
    await sc_dao.update(303, SchemeInternalUpdate(name="Monsoon Scheme"))
    assert len(sc_exec) == 1
    sql, params = sc_exec[0]
    assert "name = :s_name" in sql
    assert "cashback_percentage = :cashback_percentage" not in sql
    assert params["id"] == 303
    assert params["s_name"] == "Monsoon Scheme"

    # 5. Test MySQLSearchTagsDAO targeted dynamic update without child updates
    st_dao = search_tags_dao_mod.MySQLSearchTagsDAO()
    st_exec, st_factory = setup_mock_db()
    st_dao._factory = MagicMock(return_value=st_factory)
    st_dao.findById = AsyncMock(return_value=MagicMock())
    await st_dao.update(404, SearchTagInternalUpdate(name="Summer Collection"))
    # Only 1 query: UPDATE, no child table operations
    assert len(st_exec) == 1
    sql, params = st_exec[0]
    assert "name = :s_name" in sql
    assert "type = :s_type" not in sql
    assert "is_active = :s_is_active" not in sql
    assert params["id"] == 404
    assert params["s_name"] == "Summer Collection"

    # 6. Test MySQLSearchTagsDAO targeted dynamic update WITH child updates
    st_exec2, st_factory2 = setup_mock_db()
    st_dao._factory = MagicMock(return_value=st_factory2)
    st_dao.findById = AsyncMock(return_value=MagicMock())
    await st_dao.update(404, SearchTagInternalUpdate(categories=["cat1", "cat2"]))
    # UPDATE query + DELETE categories + INSERT cat1 + INSERT cat2
    assert len(st_exec2) == 4
    cat_del_sql = st_exec2[1][0]
    assert "DELETE FROM sj_search_tag_categories" in cat_del_sql
    cat_ins_sql = st_exec2[2][0]
    assert "INSERT INTO sj_search_tag_categories" in cat_ins_sql


@pytest.mark.asyncio
async def test_settings_and_content_daos_targeted_dynamic_updates_and_zero_dict():
    import app.db.mysql_aboutUs_dao as about_dao_mod
    import app.db.mysql_privacyPolicy_dao as privacy_dao_mod
    import app.db.mysql_systemSettings_dao as sys_dao_mod
    import app.db.mysql_valetPayoutSettings_dao as valet_payout_dao_mod

    from app.models.daos_flat import (
        AboutUsInternalUpdate,
        PrivacyPolicyInternalUpdate,
        ValetPayoutSettingsInternalUpdate,
    )
    from app.models.system_settings import SystemSettingsUpdate

    # 1. AST Check: Zero reflection calls, zero dict in signatures, zero isdigit
    modules_to_check = [about_dao_mod, privacy_dao_mod, sys_dao_mod, valet_payout_dao_mod]
    for mod in modules_to_check:
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"getattr", "setattr", "hasattr"}:
                assert False, f"Found reflection call {node.func.id} in {mod.__name__}"
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    if arg.annotation and isinstance(arg.annotation, ast.Name):
                        assert arg.annotation.id not in {"dict", "Dict"}, f"Found dict/Dict parameter in {mod.__name__}.{node.name}"

        assert "isdigit" not in src, f"Found isdigit in {mod.__name__}"

    # Helper for DB mock
    def setup_mock_db():
        executed = []
        mock_session = AsyncMock()
        mock_res = MagicMock()
        mock_res.rowcount = 1

        async def fake_exec(stmt, p=None):
            executed.append((str(stmt), p or {}))
            return mock_res

        mock_session.execute = fake_exec
        mock_session.commit = AsyncMock()

        class MockCtx:
            async def __aenter__(self):
                return mock_session
            async def __aexit__(self, *args):
                pass

        return executed, lambda: MockCtx()

    # 2. Test MySQLAboutUsDAO targeted dynamic update
    about_dao = about_dao_mod.MySQLAboutUsDAO()
    about_exec, about_factory = setup_mock_db()
    about_dao._factory = MagicMock(return_value=about_factory)
    about_dao.findById = AsyncMock(return_value=MagicMock())
    await about_dao.update(1, AboutUsInternalUpdate(title="About Us New"))
    assert len(about_exec) == 1
    sql, params = about_exec[0]
    assert "title = :title" in sql
    assert "content = :content" not in sql
    assert "version = :version" not in sql
    assert "is_published = :isPublished" not in sql
    assert params["id"] == 1
    assert params["title"] == "About Us New"

    # 3. Test MySQLPrivacyPolicyDAO targeted dynamic update
    privacy_dao = privacy_dao_mod.MySQLPrivacyPolicyDAO()
    p_exec, p_factory = setup_mock_db()
    privacy_dao._factory = MagicMock(return_value=p_factory)
    privacy_dao.findById = AsyncMock(return_value=MagicMock())
    await privacy_dao.update(1, PrivacyPolicyInternalUpdate(version="2.0"))
    assert len(p_exec) == 1
    sql, params = p_exec[0]
    assert "version = :version" in sql
    assert "content = :content" not in sql
    assert "effective_date = :effectiveDate" not in sql
    assert "is_active = :isActive" not in sql
    assert params["id"] == 1
    assert params["version"] == "2.0"

    # 4. Test MySQLSystemSettingsDAO targeted dynamic update
    sys_dao = sys_dao_mod.MySQLSystemSettingsDAO()
    s_exec, s_factory = setup_mock_db()
    sys_dao._factory = MagicMock(return_value=s_factory)
    sys_dao.findById = AsyncMock(return_value=MagicMock())
    await sys_dao.update(1, SystemSettingsUpdate(maintenance_mode=True))
    assert len(s_exec) == 1
    sql, params = s_exec[0]
    assert "maintenance_mode = :maintenanceMode" in sql
    assert "allow_signups = :allowSignups" not in sql
    assert "max_upload_size_mb = :maxUploadSizeMb" not in sql
    assert "default_currency = :defaultCurrency" not in sql
    assert "timezone = :timezone" not in sql
    assert params["id"] == 1
    assert params["maintenanceMode"] == 1

    # 5. Test MySQLValetPayoutSettingsDAO targeted dynamic update
    valet_dao = valet_payout_dao_mod.MySQLValetPayoutSettingsDAO()
    v_exec, v_factory = setup_mock_db()
    valet_dao._factory = MagicMock(return_value=v_factory)
    valet_dao.findById = AsyncMock(return_value=MagicMock())
    await valet_dao.update(1, ValetPayoutSettingsInternalUpdate(delivery_charge_per_order=45.0))
    assert len(v_exec) == 1
    sql, params = v_exec[0]
    assert "delivery_charge_per_order = :deliveryChargePerOrder" in sql
    assert "return_pickup_charge_per_order = :returnPickupChargePerOrder" not in sql
    assert params["id"] == 1
    assert params["deliveryChargePerOrder"] == 45.0

