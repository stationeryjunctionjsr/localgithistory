import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError

from app.models.daos import WishlistItemInternal, WishlistInternalCreate, WishlistInternalUpdate
from app.models.wishlist import Wishlist
from app.db.mysql_wishlist_dao import MySQLWishlistDAO
from app.repositories.wishlist_repository import WishlistRepository
from app.routers.wishlist import WishlistItemRequest


def test_wishlist_item_internal_pure_int():
    item = WishlistItemInternal(id=1, product=100, quantity=2)
    assert item.id == 1
    assert item.product == 100
    assert item.quantity == 2

    # Verify legacy _id or string products raise ValidationError
    with pytest.raises(ValidationError):
        WishlistItemInternal(product=100, _id=1)


def test_wishlist_model_no_legacy_fields():
    w = Wishlist(id=5, user=42, items=[WishlistItemInternal(id=1, product=99)])
    assert w.id == 5
    assert w.user == 42
    assert len(w.items) == 1
    assert w.items[0].product == 99
    assert not hasattr(w, "_id")
    assert not hasattr(w, "wid")
    assert not hasattr(w, "pid")


def test_wishlist_dao_map_to_schema_native_ints():
    dao = MySQLWishlistDAO()
    row = SimpleNamespace(id=10, user_id=20, created_at=None, updated_at=None)
    items_rows = [
        SimpleNamespace(wishlist_id=10, product_id=101),
        SimpleNamespace(wishlist_id=10, product_id=102),
        SimpleNamespace(wishlist_id=99, product_id=999),
    ]

    mapped = dao._map_to_schema(row, items_rows)
    assert mapped.id == 10
    assert mapped.user == 20
    assert len(mapped.items) == 2
    assert mapped.items[0].product == 101
    assert isinstance(mapped.items[0].product, int)
    assert mapped.items[1].product == 102
    assert isinstance(mapped.items[1].product, int)


@pytest.mark.asyncio
async def test_wishlist_dao_replace_items_pure_int_bindings():
    dao = MySQLWishlistDAO()
    session = MagicMock()
    session.execute = AsyncMock()

    items = [
        WishlistItemInternal(product=42),
        WishlistItemInternal(product=88),
    ]

    await dao._replace_items(session, 10, items)

    assert session.execute.call_count == 3  # 1 DELETE + 2 INSERT
    # Check parameters passed to INSERT
    calls = session.execute.call_args_list
    assert calls[1][0][1] == {"wid": 10, "pid": 42}
    assert isinstance(calls[1][0][1]["pid"], int)
    assert calls[2][0][1] == {"wid": 10, "pid": 88}
    assert isinstance(calls[2][0][1]["pid"], int)


@pytest.mark.asyncio
async def test_wishlist_repository_remove_item_int():
    repo = WishlistRepository()
    mock_storage = MagicMock()
    existing_wishlist = Wishlist(
        id=1,
        user=10,
        items=[
            WishlistItemInternal(product=100),
            WishlistItemInternal(product=200),
        ],
    )
    mock_storage.findOne = AsyncMock(return_value=existing_wishlist)
    mock_storage.update = AsyncMock()
    repo.storage = mock_storage

    result = await repo.removeItem(user_id=10, product_id=100)
    assert result is True
    mock_storage.update.assert_called_once()
    updated_data = mock_storage.update.call_args[0][1]
    assert len(updated_data.items) == 1
    assert updated_data.items[0].product == 200


def test_wishlist_item_request_pydantic_native_int():
    req = WishlistItemRequest.model_validate({"productId": 55, "sessionId": "sess-1"})
    assert req.product_id == 55
    assert isinstance(req.product_id, int)
