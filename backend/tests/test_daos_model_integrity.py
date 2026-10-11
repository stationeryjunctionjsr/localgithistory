import ast
import inspect
import pytest
from pydantic import ValidationError

import app.models.daos as daos_mod
from app.models.daos import (
    CartItemInternal,
    WishlistItemInternal,
    SessionInternalCreate,
    SessionInternalUpdate,
    ProductInternalCreate,
    ReturnRequestInternalCreate,
    ReturnRequestInternal,
    CustomerSegmentInternalCreate,
    NotificationInternalCreate,
    NotificationInternal,
    OrderFilter,
)


def test_zero_alias_id_in_daos_models():
    source = inspect.getsource(daos_mod)
    tree = ast.parse(source)

    # Verify no alias="_id" or alias='_id' in AST
    alias_id_nodes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "alias":
            if isinstance(node.value, ast.Constant) and node.value.value == "_id":
                alias_id_nodes.append(node)

    assert len(alias_id_nodes) == 0, f"Found alias='_id' in daos.py: {len(alias_id_nodes)} instances"


def test_product_internal_create_forbids_extra_fields():
    # Verify extra='forbid'
    assert daos_mod.ProductInternalCreate.model_config.get("extra") == "forbid"

    # Should succeed with valid fields
    valid_p = ProductInternalCreate(name="Notebook", price=50.0)
    assert valid_p.name == "Notebook"
    assert valid_p.price == 50.0

    # Should raise ValidationError when unexpected extra field is passed
    with pytest.raises(ValidationError):
        ProductInternalCreate(name="Notebook", unknown_field="invalid")


def test_cart_item_internal_strict_fields():
    item = CartItemInternal(id="item-123", product="prod-456", quantity=2)
    assert item.id == "item-123"
    assert item.product == "prod-456"
    assert item.quantity == 2
    assert not hasattr(item, "id_")

    with pytest.raises(ValidationError):
        CartItemInternal(product="prod-456", _id="legacy-id")


def test_wishlist_item_internal_strict_fields():
    item = WishlistItemInternal(id="wl-1", product="prod-99")
    assert item.id == "wl-1"
    assert item.product == "prod-99"
    assert not hasattr(item, "id_")

    with pytest.raises(ValidationError):
        WishlistItemInternal(product="prod-99", _id="legacy-id")


def test_session_internal_models_cleaned():
    sess_create = SessionInternalCreate(user="usr-1", ip_address="127.0.0.1")
    assert sess_create.user == "usr-1"
    assert not hasattr(sess_create, "eid")
    assert not hasattr(sess_create, "deletedCount")

    sess_update = SessionInternalUpdate(is_active=False)
    assert sess_update.is_active is False
    assert not hasattr(sess_update, "eid")
    assert not hasattr(sess_update, "deletedCount")
    assert not hasattr(sess_update, "id_")


def test_return_request_models_purged():
    ret_create = ReturnRequestInternalCreate(id="ret-1", order_id="ord-1")
    assert ret_create.id == "ret-1"
    assert ret_create.order_id == "ord-1"

    ret_int = ReturnRequestInternal(id="ret-2", order_id="ord-2")
    assert ret_int.id == "ret-2"


def test_customer_segment_and_notification_purged():
    seg = CustomerSegmentInternalCreate(id="seg-1", name="VIP", type="manual", userIds=["u1"])
    assert seg.id == "seg-1"

    notif_create = NotificationInternalCreate(
        id="notif-1", user_id="u1", type="order", title="Shipped", message="Your order shipped"
    )
    assert notif_create.id == "notif-1"

    notif = NotificationInternal(
        id="notif-2", user_id="u1", type="order", title="Delivered", message="Order delivered", is_read=False, is_acknowledged=False
    )
    assert notif.id == "notif-2"


def test_order_filter_model():
    # Test by field names
    f1 = OrderFilter(id="10", user_id="usr-5", status="pending")
    assert f1.id == "10"
    assert f1.user_id == "usr-5"
    assert f1.status == "pending"

    # Test automatic CamelBaseModel aliases (to_camel)
    f2 = OrderFilter.model_validate({
        "userId": "usr-5",
        "orderType": "delivery",
        "paymentMethod": "cod",
        "startDate": "2026-01-01T00:00:00Z",
        "endDate": "2026-01-02T00:00:00Z",
        "orderNumberPrefix": "ORD-",
        "idempotencyKey": "key-xyz",
        "assignedValet": "valet-1",
    })
    assert f2.user_id == "usr-5"
    assert f2.order_type == "delivery"
    assert f2.payment_method == "cod"
    assert f2.order_number_prefix == "ORD-"
    assert f2.idempotency_key == "key-xyz"
    assert f2.assigned_valet == "valet-1"

    # Extra fields must be forbidden
    with pytest.raises(ValidationError):
        OrderFilter.model_validate({"unknown_filter": "bad"})
