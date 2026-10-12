import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.daos_flat import SearchTagInternal, SearchTagInternalCreate, SearchTagInternalUpdate
from app.models.schemas import SearchTagCreate, SearchTagUpdate, SearchTagResponse
from app.models.product import Product
from app.repositories.search_tag_repository import search_tag_repository
from app.repositories.product_repository import product_repository
from app.db.mysql_searchTags_dao import MySQLSearchTagsDAO
from app.routers.products import (
    ProductTagAction,
    ProductSearchTagsResponse,
    add_search_tag_to_product,
    remove_search_tag_from_product,
    get_product_search_tags,
)


def test_search_tag_internal_models_integer_product_ids():
    """Verify that SearchTag models enforce integer product IDs natively."""
    tag = SearchTagInternal(
        id=1,
        tag_id="ST-1",
        name="Summer",
        type="Occasion",
        is_active=True,
        product_ids=[101, 102],
        excluded_product_ids=[201],
    )
    assert tag.product_ids == [101, 102]
    assert tag.excluded_product_ids == [201]

    create_model = SearchTagInternalCreate(
        name="Winter",
        type="Occasion",
        product_ids=[301],
        excluded_product_ids=[401],
    )
    assert create_model.product_ids == [301]
    assert create_model.excluded_product_ids == [401]

    update_model = SearchTagInternalUpdate(
        product_ids=[501, 502],
        excluded_product_ids=[601],
    )
    assert update_model.product_ids == [501, 502]
    assert update_model.excluded_product_ids == [601]


def test_mysql_search_tags_dao_map_to_schema_no_int_shim():
    """Verify that _map_to_schema directly maps child rows without Python int() casts."""
    dao = MySQLSearchTagsDAO()

    mock_row = MagicMock()
    mock_row.id = 5
    mock_row.tag_id = "ST-5"
    mock_row.name = "Party"
    mock_row.type = "Occasion"
    mock_row.is_active = 1
    mock_row.created_at = None
    mock_row.updated_at = None

    prod_child = MagicMock()
    prod_child.parent_id = 5
    prod_child.product_id = 1001

    ex_prod_child = MagicMock()
    ex_prod_child.parent_id = 5
    ex_prod_child.product_id = 2002

    child_rows = ([], [], [], [], [prod_child], [ex_prod_child])
    schema = dao._map_to_schema(mock_row, child_rows)

    assert schema.id == 5
    assert schema.product_ids == [1001]
    assert schema.excluded_product_ids == [2002]
    assert isinstance(schema.product_ids[0], int)
    assert isinstance(schema.excluded_product_ids[0], int)


@pytest.mark.asyncio
async def test_search_tag_repository_add_and_exclude_product_id():
    """Verify addProductId and excludeProductId operate natively with int product IDs."""
    existing_tag = SearchTagInternal(
        id=10,
        tag_id="ST-10",
        name="Trending",
        type="Intent",
        is_active=True,
        product_ids=[101],
        excluded_product_ids=[202],
    )

    with patch.object(search_tag_repository, "findById", new_callable=AsyncMock) as mock_find:
        with patch.object(search_tag_repository, "update", new_callable=AsyncMock) as mock_update:
            mock_find.return_value = existing_tag
            mock_update.return_value = existing_tag

            # Add product 202: should be added to product_ids, removed from excluded_product_ids
            await search_tag_repository.addProductId(10, 202)
            mock_update.assert_called_once()
            call_args = mock_update.call_args[0]
            assert call_args[0] == 10
            update_payload: SearchTagInternalUpdate = call_args[1]
            assert 202 in update_payload.product_ids
            assert 202 not in update_payload.excluded_product_ids

            mock_update.reset_mock()

            # Exclude product 101: should be added to excluded_product_ids, removed from product_ids
            await search_tag_repository.excludeProductId(10, 101)
            mock_update.assert_called_once()
            call_args = mock_update.call_args[0]
            assert call_args[0] == 10
            update_payload_ex: SearchTagInternalUpdate = call_args[1]
            assert 101 in update_payload_ex.excluded_product_ids
            assert 101 not in update_payload_ex.product_ids


@pytest.mark.asyncio
async def test_product_repository_resolve_search_tags_native_int():
    """Verify resolve_search_tags matches products using native integer IDs without str casts."""
    product = Product(
        id="101",
        product_id=101,
        name="Cotton Shirt",
        category="Apparel",
    )

    tag_assigned = SearchTagInternal(
        id=1,
        tag_id="ST-1",
        name="Assigned Tag",
        type="Occasion",
        is_active=True,
        product_ids=[101],
        excluded_product_ids=[],
    )

    tag_excluded = SearchTagInternal(
        id=2,
        tag_id="ST-2",
        name="Excluded Tag",
        type="Occasion",
        is_active=True,
        categories=["Apparel"],
        excluded_product_ids=[101],
    )

    with patch.object(product_repository, "_get_active_search_tags", new_callable=AsyncMock) as mock_tags:
        with patch.object(product_repository, "_get_collections", new_callable=AsyncMock) as mock_cols:
            mock_tags.return_value = [tag_assigned, tag_excluded]
            mock_cols.return_value = []

            resolved = await product_repository.resolve_search_tags([product])
            assert len(resolved) == 1
            assert "Assigned Tag" in resolved[0].search_tags
            assert "Excluded Tag" not in resolved[0].search_tags


@pytest.mark.asyncio
async def test_router_product_search_tags_endpoints():
    """Verify router endpoints handle native integer IDs cleanly."""
    mock_product = Product(id="101", product_id=101, name="Test")
    mock_tag = SearchTagInternal(id=5, name="Featured", type="Occasion", is_active=True)

    with patch.object(product_repository, "findById", new_callable=AsyncMock) as mock_find:
        with patch.object(product_repository, "resolve_search_tags", new_callable=AsyncMock) as mock_resolve:
            with patch("app.repositories.search_tag_repository.search_tag_repository.addProductId", new_callable=AsyncMock) as mock_add:
                with patch("app.repositories.search_tag_repository.search_tag_repository.excludeProductId", new_callable=AsyncMock) as mock_ex:
                    with patch("app.repositories.search_tag_repository.search_tag_repository.findAllActive", new_callable=AsyncMock) as mock_active:
                        mock_find.return_value = mock_product
                        mock_product.search_tags = ["Featured"]
                        mock_resolve.return_value = [mock_product]
                        mock_add.return_value = mock_tag
                        mock_ex.return_value = mock_tag
                        mock_active.return_value = [mock_tag]

                        mock_admin = MagicMock()

                        # Test add
                        action = ProductTagAction(search_tag_id=5)
                        add_res = await add_search_tag_to_product(101, action, mock_admin)
                        assert add_res["message"] == "Search tag added to product"
                        mock_add.assert_called_once_with(5, 101)

                        # Test remove
                        rem_res = await remove_search_tag_from_product(101, 5, mock_admin)
                        assert rem_res["message"] == "Search tag removed from product"
                        mock_ex.assert_called_once_with(5, 101)

                        # Test get
                        get_res = await get_product_search_tags(101, mock_admin)
                        assert get_res["resolvedTags"] == ["Featured"]
                        assert get_res["allTags"] == [{"id": 5, "name": "Featured", "type": "Occasion"}]
