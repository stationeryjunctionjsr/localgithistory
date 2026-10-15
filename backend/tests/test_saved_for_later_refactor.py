import inspect
from typing import Optional
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.db.mysql_saved_for_later_dao import MySQLSavedForLaterDAO
import app.db.mysql_saved_for_later_dao as dao_mod
from app.models.saved_for_later import SavedForLater, SavedForLaterItem
from app.repositories.cart_repository import CartRepository
import app.repositories.cart_repository as repo_mod


def test_saved_for_later_no_union_no_dict_no_str_shims():
    dao_src = inspect.getsource(dao_mod)
    assert "Union" not in dao_src, "No Union allowed in MySQLSavedForLaterDAO"
    assert "dict[" not in dao_src, "No dict grouping allowed in MySQLSavedForLaterDAO"
    assert "str(user_id)" not in dao_src, "No str(user_id) casting allowed in MySQLSavedForLaterDAO"
    assert "str(product_id)" not in dao_src, "No str(product_id) casting allowed in MySQLSavedForLaterDAO"

    repo_src = inspect.getsource(repo_mod.CartRepository.saveForLater)
    assert "Union" not in repo_src, "No Union allowed in saveForLater"
    assert "product_id: int" in repo_src, "product_id must be native int in saveForLater"

    # Schema model checks
    assert SavedForLaterItem.model_fields["user"].annotation is Optional[int]
    assert SavedForLaterItem.model_fields["product_id"].annotation is Optional[int]
    assert SavedForLater.model_fields["user"].annotation is Optional[int]


@pytest.mark.asyncio
async def test_saved_for_later_granular_diff_and_atomic_methods():
    dao = MySQLSavedForLaterDAO()

    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    with patch("app.db.mysql_saved_for_later_dao.get_async_session_factory", return_value=mock_factory):
        # 1. add_item: test when item is new
        mock_chk = MagicMock()
        mock_chk.scalar.return_value = None
        mock_session.execute.return_value = mock_chk

        added = await dao.add_item(101, 100)
        assert added is True
        query_add = str(mock_session.execute.call_args[0][0])
        assert "INSERT INTO sj_saved_for_later" in query_add
        assert mock_session.commit.called
        params_add = mock_session.execute.call_args[0][1]
        assert params_add["user_id"] == 101
        assert params_add["product_id"] == 100
        assert isinstance(params_add["user_id"], int)
        assert isinstance(params_add["product_id"], int)

        # 2. remove_item
        mock_del_res = MagicMock()
        mock_del_res.rowcount = 1
        mock_session.execute.return_value = mock_del_res
        removed = await dao.remove_item(101, 100)
        assert removed is True
        query_rem = str(mock_session.execute.call_args[0][0])
        assert "DELETE FROM sj_saved_for_later WHERE user_id = :uid AND product_id = :pid" in query_rem
        params_rem = mock_session.execute.call_args[0][1]
        assert params_rem["uid"] == 101
        assert params_rem["pid"] == 100
        assert isinstance(params_rem["uid"], int)
        assert isinstance(params_rem["pid"], int)

        # 3. update() with diffing: existing has 1, new payload has 1 and 2
        mock_session.reset_mock()
        row_p1 = MagicMock()
        row_p1.product_id = 1
        row_p1.saved_at = None
        row_p1.created_at = None
        mock_res_exist = MagicMock()
        mock_res_exist.fetchall.return_value = [row_p1]
        mock_session.execute.return_value = mock_res_exist

        update_data = SavedForLater(user=101, items=[
            SavedForLaterItem(product_id=1),
            SavedForLaterItem(product_id=2),
        ])
        await dao.update(101, update_data)

        # Inspect execute calls during update
        calls = [str(c[0][0]) for c in mock_session.execute.call_args_list]
        assert any("SELECT product_id FROM sj_saved_for_later" in c for c in calls)
        assert not any("DELETE FROM sj_saved_for_later WHERE user_id = :uid\n" in c for c in calls)
        insert_calls = [c for c in calls if "INSERT INTO sj_saved_for_later" in c]
        assert len(insert_calls) == 1


@pytest.mark.asyncio
async def test_cart_repository_save_for_later_atomic():
    repo = CartRepository()
    mock_dao = MagicMock()
    mock_dao.add_item = AsyncMock(return_value=True)
    mock_dao.findOne = AsyncMock(return_value=SavedForLater(user=101, items=[SavedForLaterItem(product_id=1)]))

    with patch("app.repositories.cart_repository.get_storage", return_value=mock_dao):
        result = await repo.saveForLater(101, 1)
        mock_dao.add_item.assert_awaited_once_with(101, 1)
        assert result is not None
        assert result.user == 101
        assert isinstance(result.user, int)
