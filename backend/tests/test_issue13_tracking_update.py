import pytest
import typing
from app.db.mysql_tracking_dao import MySQLTrackingDAO


@pytest.mark.asyncio
async def test_issue13_tracking_dao_update_raises_not_implemented():
    """Verify MySQLTrackingDAO.update explicitly raises NotImplementedError instead of silently returning stale record."""
    dao = MySQLTrackingDAO()

    with pytest.raises(NotImplementedError) as exc_info:
        await dao.update(1, {"event": "updated"})

    assert "strictly append-only" in str(exc_info.value).lower()

    # Also verify type hints evaluate without forward reference crashes
    hints = typing.get_type_hints(dao.update)
    assert "return" in hints
