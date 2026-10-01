try:
    from app.models.daos import NotificationInternalCreate
except ImportError:
    pass
try:
    from app.models.daos_flat import NotificationInternalCreate
except ImportError:
    pass
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.repositories.notification_repository import notification_repository

# Generate unique prefix per test run to prevent clashes in persistent DB
PREFIX = f"TEST_OPT_{uuid.uuid4().hex[:8]}_"

@pytest.fixture(autouse=True)
async def cleanup_notifications():
    yield
    try:
        notifs = await notification_repository.storage.findAll()
        for n in notifs:
            if (n.get("title") or "").startswith(PREFIX):
                await notification_repository.storage.delete(n["_id"])
    except Exception:
        pass


@pytest.mark.asyncio
async def test_notification_optimizations():
    # 1. Create a set of test notifications with distinct attributes
    n1 = await notification_repository.create(
        NotificationInternalCreate(**{'_id': __import__('uuid').uuid4().hex, **{"title": f"{PREFIX}1", "message": "Message 1", "userId": "user_opt_A", "type": "new_order"}})
    )
    n2 = await notification_repository.create(
        NotificationInternalCreate(**{'_id': __import__('uuid').uuid4().hex, **{"title": f"{PREFIX}2", "message": "Message 2", "userId": "user_opt_A", "type": "low_stock"}})
    )
    n3 = await notification_repository.create(
        NotificationInternalCreate(**{'_id': __import__('uuid').uuid4().hex, **{"title": f"{PREFIX}3", "message": "Message 3", "userId": "user_opt_B", "type": "new_order"}})
    )

    # Initially all should be unread and unacknowledged
    assert n1.is_read is False
    assert n1["isAcknowledged"] is False
    assert n2["isRead"] is False
    assert n3["isRead"] is False

    # 2. Test findById direct retrieval
    retrieved_n1 = await notification_repository.findById(n1["_id"])
    assert retrieved_n1 is not None
    assert retrieved_n1["title"] == f"{PREFIX}1"

    # 3. Test findAll with filters (exact filtering at DB level)
    # Filter by userId
    user_A_notifs = await notification_repository.findAll({"userId": "user_opt_A"})
    # Filter to only the test ones
    user_A_notifs = [n for n in user_A_notifs if (n.get("title") or "").startswith(PREFIX)]
    assert len(user_A_notifs) == 2
    assert {n["title"] for n in user_A_notifs} == {f"{PREFIX}1", f"{PREFIX}2"}

    # Filter by type
    low_stock_notifs = await notification_repository.findAll({"type": "low_stock"})
    low_stock_notifs = [n for n in low_stock_notifs if (n.get("title") or "").startswith(PREFIX)]
    assert len(low_stock_notifs) == 1
    assert low_stock_notifs[0]["title"] == f"{PREFIX}2"

    # Filter by isRead
    unread_notifs = await notification_repository.findAll({"isRead": False})
    unread_notifs = [n for n in unread_notifs if (n.get("title") or "").startswith(PREFIX)]
    assert len(unread_notifs) == 3

    # 4. Test acknowledge and markAsRead single operations
    updated_n2 = await notification_repository.markAsRead(n2["_id"])
    assert updated_n2["isRead"] is True
    assert updated_n2["isAcknowledged"] is False  # Acknowledge is still False

    updated_n3 = await notification_repository.acknowledge(n3["_id"])
    assert updated_n3["isRead"] is False
    assert updated_n3["isAcknowledged"] is True

    # 5. Test markAllAsRead bulk operation
    count = await notification_repository.markAllAsRead()

    # Check that it returns the count of updated notifications (at least 3 in this case)
    assert count >= 3

    # Verify all are now read and acknowledged
    all_notifs = await notification_repository.findAll()
    test_notifs = [n for n in all_notifs if (n.get("title") or "").startswith(PREFIX)]
    assert len(test_notifs) == 3
    for n in test_notifs:
        assert n["isRead"] is True
        assert n["isAcknowledged"] is True

    # Verify markAllAsRead returns 0 when all are already read/acknowledged
    count_zero = await notification_repository.markAllAsRead()
    assert count_zero == 0