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
    assert order.orderNumber == "ORD-101"
    assert order.valetCascadeCount == 2
    assert len(order.valetDeclineHistory) == 1
    assert order.valetDeclineHistory[0].valet_id == "valet1"
    assert order.valetAssignedAt is not None

def test_return_request_properties_and_decline_history():
    """Verify ReturnRequestInternal exposes properties for cascade/revert workflows."""
    ret = ReturnRequestInternal(
        id="1",
        return_id="RET-202",
        user_id="u456",
        valet_cascade_count=1,
        valet_assigned_at="2026-10-12T00:00:00Z",
        valet_decline_history=[
            ReturnRequestValetDeclineInternal(valet_id="v2", reason="timeout")
        ],
    )
    assert ret.returnId == "RET-202"
    assert ret.userId == "u456"
    assert ret.valetCascadeCount == 1
    assert ret.valetAssignedAt == "2026-10-12T00:00:00Z"
    assert len(ret.valetDeclineHistory) == 1
    assert ret.valetDeclineHistory[0].valet_id == "v2"

def test_return_request_create_properties():
    """Verify ReturnRequestInternalCreate allows setting returnId, cascade count and history."""
    ret_create = ReturnRequestInternalCreate()
    ret_create.returnId = "RET-999"
    ret_create.valetCascadeCount = 0
    ret_create.valetDeclineHistory = []
    assert ret_create.return_id == "RET-999"
    assert ret_create.valet_cascade_count == 0
    assert ret_create.valet_decline_history == []

def test_tracking_repository_get_drop_off_points_alias():
    """Verify getDropOffPoints alias exists on tracking_repository."""
    assert hasattr(tracking_repository, "getDropOffPoints")
    assert tracking_repository.getDropOffPoints == tracking_repository.getDropOffs
