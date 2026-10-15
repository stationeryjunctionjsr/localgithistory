import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.db.mysql_saved_for_later_dao import MySQLSavedForLaterDAO
from app.models.saved_for_later import SavedForLater, SavedForLaterItem
from app.repositories.cart_repository import CartRepository


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

        added = await dao.add_item(101, "prod_100")
        assert added is True
        query_add = str(mock_session.execute.call_args[0][0])
        assert "INSERT INTO sj_saved_for_later" in query_add
        assert mock_session.commit.called

        # 2. remove_item
        mock_del_res = MagicMock()
        mock_del_res.rowcount = 1
        mock_session.execute.return_value = mock_del_res
        removed = await dao.remove_item(101, "prod_100")
        assert removed is True
        query_rem = str(mock_session.execute.call_args[0][0])
        assert "DELETE FROM sj_saved_for_later WHERE user_id = :uid AND product_id = :pid" in query_rem

        # 3. update() with diffing: existing has prod_1, new payload has prod_1 and prod_2
        mock_session.reset_mock()
        row_p1 = MagicMock()
        row_p1.product_id = "prod_1"
        row_p1.saved_at = None
        row_p1.created_at = None
        mock_res_exist = MagicMock()
        mock_res_exist.fetchall.return_value = [row_p1]
        mock_session.execute.return_value = mock_res_exist

        update_data = SavedForLater(items=[
            SavedForLaterItem(product_id="prod_1"),
            SavedForLaterItem(product_id="prod_2"),
        ])
        await dao.update(101, update_data)

        # Inspect execute calls during update
        calls = [str(c[0][0]) for c in mock_session.execute.call_args_list]
        # Should have SELECT product_id
        assert any("SELECT product_id FROM sj_saved_for_later" in c for c in calls)
        # Should NOT have blanket DELETE FROM sj_saved_for_later WHERE user_id = :uid without product_id
        assert not any("DELETE FROM sj_saved_for_later WHERE user_id = :uid\n" in c for c in calls)
        # Should have INSERT for prod_2 only
        insert_calls = [c for c in calls if "INSERT INTO sj_saved_for_later" in c]
        assert len(insert_calls) == 1


@pytest.mark.asyncio
async def test_cart_repository_save_for_later_atomic():
    repo = CartRepository()
    mock_dao = MagicMock()
    mock_dao.add_item = AsyncMock(return_value=True)
    mock_dao.findOne = AsyncMock(return_value=SavedForLater(user="101", items=[SavedForLaterItem(product_id="p1")]))

    with patch("app.repositories.cart_repository.get_storage", return_value=mock_dao):
        result = await repo.saveForLater(101, "p1")
        mock_dao.add_item.assert_awaited_once_with(101, "p1")
        assert result is not None
        assert result.user == "101"
