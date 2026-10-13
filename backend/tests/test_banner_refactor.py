import ast
import inspect
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.daos import (
    BannerFilter,
    BannerInternalCreate,
    BannerInternalUpdate,
)
from app.models.schemas import BannerResponse, BannerCreate, BannerUpdate
import app.repositories.banner_repository as repo_mod
import app.db.mysql_banner_dao as banner_dao_mod
import app.routers.banners as router_mod
import archive.flat_relational_dao as flat_dao_mod


def test_zero_lambdas_and_zero_anti_patterns():
    repo_source = inspect.getsource(repo_mod)
    dao_source = inspect.getsource(banner_dao_mod)
    router_source = inspect.getsource(router_mod)
    flat_dao_source = inspect.getsource(flat_dao_mod)

    trees = {
        "repo": ast.parse(repo_source),
        "dao": ast.parse(dao_source),
        "router": ast.parse(router_source),
        "flat_dao": ast.parse(flat_dao_source),
    }

    # 1. Zero lambdas across all components
    for name, tree in trees.items():
        lambdas = [n for n in ast.walk(tree) if isinstance(n, ast.Lambda)]
        assert len(lambdas) == 0, f"Found lambdas in {name}: {lambdas}"

    # 2. Zero reflection calls (getattr, setattr, hasattr)
    for name in ("repo", "dao", "router", "flat_dao"):
        reflection_calls = [
            n.func.id
            for n in ast.walk(trees[name])
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"getattr", "setattr", "hasattr"}
        ]
        assert len(reflection_calls) == 0, f"Found reflection calls in {name}: {reflection_calls}"

    # 3. Zero **kwargs in DAO and repo method definitions
    for name in ("repo", "dao"):
        kwargs_defs = [
            n.name
            for n in ast.walk(trees[name])
            if isinstance(n, ast.FunctionDef) and n.args.kwarg is not None
        ]
        assert len(kwargs_defs) == 0, f"Found **kwargs in {name}: {kwargs_defs}"

    # 4. Zero document-store legacy methods (deleteMany, updateMany)
    for name in ("repo", "dao", "flat_dao"):
        docstore_methods = [
            n.name
            for n in ast.walk(trees[name])
            if isinstance(n, ast.FunctionDef) and n.name in {"deleteMany", "updateMany"}
        ]
        assert len(docstore_methods) == 0, f"Found legacy docstore methods in {name}: {docstore_methods}"

    # 5. Zero in-memory accumulators (_mapping, setdefault)
    dao_acc = [
        n.attr
        for n in ast.walk(trees["dao"])
        if isinstance(n, ast.Attribute) and n.attr in {"_mapping", "setdefault"}
    ]
    assert len(dao_acc) == 0, f"Found in-memory accumulators in dao: {dao_acc}"

    # 6. Zero dynamic string query builders (_build_where)
    for name, src in [("repo", repo_source), ("dao", dao_source), ("router", router_source), ("flat_dao", flat_dao_source)]:
        assert "_build_where" not in src, f"Found _build_where in {name}"


def test_flat_relational_dao_no_backward_compatibility_aliases():
    assert not hasattr(flat_dao_mod.FlatRelationalDAO, "find_all")
    assert not hasattr(flat_dao_mod.FlatRelationalDAO, "find_by_id")
    assert not hasattr(flat_dao_mod.FlatRelationalDAO, "find_one")


def test_banner_filter_model():
    filt = BannerFilter(
        isActive=True,
        isPublished=True,
        position="homepage",
        userRole="customer",
        zoneId="zone_123",
    )
    assert filt.is_active is True
    assert filt.is_published is True
    assert filt.position == "homepage"
    assert filt.user_role == "customer"
    assert filt.zone_id == "zone_123"


@pytest.mark.asyncio
async def test_mysql_banner_dao_sql_pushdown_and_hydration():
    dao = banner_dao_mod.MySQLBannerDAO()

    mock_row = MagicMock()
    mock_row.id = 1
    mock_row.title = "Welcome Banner"
    mock_row.description = "Discount on stationeries"
    mock_row.image_url = "https://img.example.com/b1.jpg"
    mock_row.link_url = "/category/stationery"
    mock_row.display_order = 5
    mock_row.start_date = "2026-01-01T00:00:00"
    mock_row.end_date = "2026-12-31T23:59:59"
    mock_row.is_active = 1
    mock_row.is_published = 1
    mock_row.target_audience = "customer"
    mock_row.position = "homepage"
    mock_row.created_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    mock_row.updated_at = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    mock_row.zone_ids = '["zone_1", "zone_2"]'
    mock_row.user_segments_json = '["customer"]'
    mock_row.visibility_rules_json = '[]'

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result

    session_ctx = MagicMock()
    session_ctx.__aenter__.return_value = mock_session
    session_ctx.__aexit__.return_value = None

    with patch.object(dao, "_factory", return_value=MagicMock(return_value=session_ctx)):
        banners = await dao.findAll(is_active=True, is_published=True)

    assert len(banners) == 1
    assert banners[0].id == "1"
    assert banners[0].title == "Welcome Banner"
    assert banners[0].zone_ids == ["zone_1", "zone_2"]
    assert banners[0].display_order == 5
    assert banners[0].user_segments == ["customer"]

    # Exactly 1 pushdown SQL query executed (zero secondary queries)
    assert mock_session.execute.call_count == 1
    sql_executed = str(mock_session.execute.call_args[0][0])
    assert "JSON_ARRAYAGG" in sql_executed
    assert "ORDER BY b.display_order ASC, b.id ASC" in sql_executed
    assert "b.is_active = :is_active" in sql_executed
    assert "b.is_published = :is_published" in sql_executed


@pytest.mark.asyncio
async def test_banner_repository_find_active_zone_filtering():
    repo = repo_mod.banner_repository

    banner1 = BannerResponse(
        id="1",
        imageUrl="https://img.example.com/1.jpg",
        displayOrder=1,
        isActive=True,
        isPublished=True,
        position="homepage",
        userSegments=["customer"],
        zoneIds=["zone_a"],
        updatedAt=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    banner2 = BannerResponse(
        id="2",
        imageUrl="https://img.example.com/2.jpg",
        displayOrder=2,
        isActive=True,
        isPublished=True,
        position="homepage",
        userSegments=["customer"],
        zoneIds=["zone_b"],
        updatedAt=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    with patch.object(repo.storage, "findAll", new=AsyncMock(return_value=[banner1, banner2])):
        filt = BannerFilter(userRole="customer", position="homepage", zoneId="zone_a")
        res = await repo.findActive(filt, zone_id="zone_a")

        assert len(res) == 1
        assert res[0].id == "1"
        assert res[0].zone_ids == ["zone_a"]


@pytest.mark.asyncio
async def test_banner_repository_create_and_update():
    repo = repo_mod.banner_repository

    created_banner = BannerResponse(
        id="10",
        title="Promo",
        imageUrl="https://img.example.com/promo.jpg",
        displayOrder=1,
        isActive=True,
        isPublished=True,
        position="homepage",
        updatedAt=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    with patch.object(repo.storage, "create", new=AsyncMock(return_value=created_banner)) as mock_create, \
         patch.object(repo.storage, "update", new=AsyncMock(return_value=created_banner)) as mock_update:

        create_in = BannerCreate(
            title="Promo",
            imageUrl="https://img.example.com/promo.jpg",
            displayOrder=1,
            isActive=True,
            isPublished=True,
            position="homepage",
        )
        res_create = await repo.create(create_in)
        assert res_create.id == "10"
        created_arg: BannerInternalCreate = mock_create.call_args[0][0]
        assert created_arg.image_url == "https://img.example.com/promo.jpg"
        assert created_arg.display_order == 1

        update_in = BannerUpdate(
            title="Promo Updated",
            imageUrl="https://img.example.com/promo2.jpg",
            displayOrder=2,
        )
        res_update = await repo.update("10", update_in)
        assert res_update.id == "10"
        update_arg: BannerInternalUpdate = mock_update.call_args[0][1]
        assert update_arg.image_url == "https://img.example.com/promo2.jpg"
        assert update_arg.display_order == 2
