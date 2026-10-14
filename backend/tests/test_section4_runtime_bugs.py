import pytest
from datetime import datetime, timezone
from app.db.storage_factory import get_storage
from app.db.mysql_activities_dao import MySQLActivitiesDAO
from app.repositories.activity_repository import activity_repository
from app.repositories.tracking_repository import tracking_repository
from app.models.order import Order, ValetDeclineHistoryEntry
from app.models.daos_flat import (
    ActivityInternalCreate,
    ActivityInternalUpdate,
    ReturnRequestInternal,
    ReturnRequestInternalCreate,
    ReturnRequestValetDeclineInternal,
)

def test_storage_factory_resolves_activities_and_events():
    """Verify storage_factory maps 'activities' and 'events' cleanly."""
    act_store = get_storage("activities")
    assert isinstance(act_store, MySQLActivitiesDAO)

    events_store = get_storage("events")
    assert events_store is not None

def test_activity_models_accept_comments():
    """Verify Activity models accept comments without validation errors."""
    create = ActivityInternalCreate(
        user_id="u123",
        session_id="s123",
        action="login",
        comments="test comment",
    )
    assert create.comments == "test comment"

    update = ActivityInternalUpdate(
        user_id="u123",
        comments="updated comment",
    )
    assert update.comments == "updated comment"

def test_order_properties_and_decline_history():
    """Verify Order exposes properties matching valet timeout job expectations."""
    now = datetime.now(timezone.utc)
    order = Order(
        order_number="ORD-101",
        valet_cascade_count=2,
        valet_assigned_at=now,
        valet_decline_history=[
            ValetDeclineHistoryEntry(valetId="valet1", reason="timeout")
        ],
    )
    assert order.order_number == "ORD-101"
    assert order.valet_cascade_count == 2
    assert len(order.valet_decline_history) == 1
    assert order.valet_decline_history[0].valet_id == "valet1"
    assert order.valet_assigned_at is not None

def test_return_request_properties_and_decline_history():
    """Verify ReturnRequestInternal native fields for cascade/revert workflows."""
    ret = ReturnRequestInternal(
        id=1,
        return_id="RET-202",
        user_id=456,
        valet_cascade_count=1,
        valet_assigned_at="2026-10-12T00:00:00Z",
        valet_decline_history=[
            ReturnRequestValetDeclineInternal(valet_id="v2", reason="timeout")
        ],
    )
    assert ret.return_id == "RET-202"
    assert ret.user_id == 456
    assert ret.valet_cascade_count == 1
    assert ret.valet_assigned_at == "2026-10-12T00:00:00Z"
    assert len(ret.valet_decline_history) == 1
    assert ret.valet_decline_history[0].valet_id == "v2"

def test_return_request_create_properties():
    """Verify ReturnRequestInternalCreate allows setting return_id, cascade count and history."""
    ret_create = ReturnRequestInternalCreate()
    ret_create.return_id = "RET-999"
    ret_create.valet_cascade_count = 0
    ret_create.valet_decline_history = []
    assert ret_create.return_id == "RET-999"
    assert ret_create.valet_cascade_count == 0
    assert ret_create.valet_decline_history == []

def test_tracking_repository_get_drop_offs():
    """Verify getDropOffs exists and is callable on tracking_repository."""
    assert hasattr(tracking_repository, "getDropOffs")
    assert callable(tracking_repository.getDropOffs)
