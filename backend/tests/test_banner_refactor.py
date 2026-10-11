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
import app.db.flat_relational_dao as flat_dao_mod


def test_zero_lambdas_and_zero_build_where():
    repo_source = inspect.getsource(repo_mod)
    dao_source = inspect.getsource(banner_dao_mod)
    router_source = inspect.getsource(router_mod)
    flat_dao_source = inspect.getsource(flat_dao_mod)

    repo_tree = ast.parse(repo_source)
    dao_tree = ast.parse(dao_source)
    router_tree = ast.parse(router_source)
    flat_dao_tree = ast.parse(flat_dao_source)

    repo_lambdas = [n for n in ast.walk(repo_tree) if isinstance(n, ast.Lambda)]
    dao_lambdas = [n for n in ast.walk(dao_tree) if isinstance(n, ast.Lambda)]
    router_lambdas = [n for n in ast.walk(router_tree) if isinstance(n, ast.Lambda)]
    flat_dao_lambdas = [n for n in ast.walk(flat_dao_tree) if isinstance(n, ast.Lambda)]

    assert len(repo_lambdas) == 0, f"Found lambdas in banner_repository: {repo_lambdas}"
    assert len(dao_lambdas) == 0, f"Found lambdas in mysql_banner_dao: {dao_lambdas}"
    assert len(router_lambdas) == 0, f"Found lambdas in banners router: {router_lambdas}"
    assert len(flat_dao_lambdas) == 0, f"Found lambdas in flat_relational_dao: {flat_dao_lambdas}"

    assert "_build_where" not in repo_source
    assert "_build_where" not in dao_source
    assert "_build_where" not in router_source
    assert "_build_where" not in flat_dao_source


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
    mock_row._mapping = {
        "_id": 1,
        "external_id": "ext_1",
        "title": "Welcome Banner",
        "description": "Discount on stationeries",
        "image_url": "https://img.example.com/b1.jpg",
        "link_url": "/category/stationery",
        "display_order": 5,
        "start_date": "2026-01-01T00:00:00",
        "end_date": "2026-12-31T23:59:59",
        "is_active": 1,
        "is_published": 1,
        "target_audience": "customer",
        "position": "homepage",
        "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        "zone_ids": '["zone_1", "zone_2"]',
    }

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]

    mock_seg_result = MagicMock()
    mock_seg_result.fetchall.return_value = []

    mock_rules_result = MagicMock()
    mock_rules_result.fetchall.return_value = []

    mock_session = AsyncMock()
    mock_session.execute.side_effect = [mock_result, mock_seg_result, mock_rules_result]

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

    first_query = str(mock_session.execute.call_args_list[0][0][0])
    assert "ORDER BY display_order ASC, id ASC" in first_query
    assert "is_active = :is_active" in first_query
    assert "is_published = :is_published" in first_query


@pytest.mark.asyncio
async def test_banner_repository_find_active_zone_filtering():
    repo = repo_mod.banner_repository

    banner1 = BannerResponse(
        _id="1",
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
        _id="2",
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
