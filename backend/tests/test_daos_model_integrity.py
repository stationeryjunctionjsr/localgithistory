import ast
import inspect
import pytest
from pydantic import ValidationError

import app.models.daos as daos_mod
import app.models.daos_flat as daos_flat_mod
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


def test_zero_alias_id_in_daos_flat_models():
    source = inspect.getsource(daos_flat_mod)
    tree = ast.parse(source)

    # Verify no alias="_id", alias="externalId", or alias="sellerId" in AST
    alias_nodes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "alias":
            if isinstance(node.value, ast.Constant) and node.value.value in ("_id", "externalId", "sellerId"):
                alias_nodes.append((node.value.value, getattr(node, "lineno", None)))

    assert len(alias_nodes) == 0, f"Found legacy aliases in daos_flat.py: {alias_nodes}"


def test_zero_alias_id_in_auxiliary_models():
    import app.models.bundle as bundle_mod
    import app.models.customer_segment as customer_segment_mod
    import app.models.division as division_mod
    import app.models.email_otp as email_otp_mod
    import app.models.faq_section as faq_section_mod
    import app.models.otp as otp_mod
    import app.models.valet_availability as valet_availability_mod
    import app.models.schemas as schemas_mod
    import app.models.about_us as about_us_mod
    import app.models.brand as brand_mod
    import app.models.classification_tags as classification_tags_mod
    import app.models.coach_marks as coach_marks_mod
    import app.models.google_reviews as google_reviews_mod
    import app.models.order_feedback as order_feedback_mod
    import app.models.pincode_searches as pincode_searches_mod
    import app.models.privacy_policy as privacy_policy_mod
    import app.models.product_reviews as product_reviews_mod
    import app.models.promo_strips as promo_strips_mod
    import app.models.push_notifications as push_notifications_mod
    import app.models.return_settings as return_settings_mod
    import app.models.review_classifications as review_classifications_mod
    import app.models.system_settings as system_settings_mod
    import app.models.valet_payout_settings as valet_payout_settings_mod

    modules = [
        bundle_mod,
        customer_segment_mod,
        division_mod,
        email_otp_mod,
        faq_section_mod,
        otp_mod,
        valet_availability_mod,
        schemas_mod,
        about_us_mod,
        brand_mod,
        classification_tags_mod,
        coach_marks_mod,
        google_reviews_mod,
        order_feedback_mod,
        pincode_searches_mod,
        privacy_policy_mod,
        product_reviews_mod,
        promo_strips_mod,
        push_notifications_mod,
        return_settings_mod,
        review_classifications_mod,
        system_settings_mod,
        valet_payout_settings_mod,
    ]

    for mod in modules:
        source = inspect.getsource(mod)
        tree = ast.parse(source)
        alias_nodes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "alias":
                if isinstance(node.value, ast.Constant) and node.value.value in ("_id", "externalId"):
                    alias_nodes.append((node.value.value, getattr(node, "lineno", None)))
        assert len(alias_nodes) == 0, f"Found legacy aliases in {mod.__name__}: {alias_nodes}"


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
    item = WishlistItemInternal(id=1, product=99)
    assert item.id == 1
    assert item.product == 99
    assert not hasattr(item, "id_")

    with pytest.raises(ValidationError):
        WishlistItemInternal(product=99, _id="legacy-id")


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
    ret_create = ReturnRequestInternalCreate(id=1, order_id="ord-1")
    assert ret_create.id == 1
    assert ret_create.order_id == "ord-1"

    ret_int = ReturnRequestInternal(id=2, order_id="ord-2")
    assert ret_int.id == 2


def test_customer_segment_and_notification_purged():
    seg = CustomerSegmentInternalCreate(id="seg-1", name="VIP", type="manual", userIds=["u1"])
    assert seg.id == "seg-1"

    notif_create = NotificationInternalCreate(
        id=1, user_id="u1", type="order", title="Shipped", message="Your order shipped"
    )
    assert notif_create.id == 1

    notif = NotificationInternal(
        id=2, user_id="u1", type="order", title="Delivered", message="Order delivered", is_read=False, is_acknowledged=False
    )
    assert notif.id == 2


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


def test_user_filter_model_strict_typing():
    from app.models.user import UserFilter

    # Valid instantiation
    uf = UserFilter(role="customer", is_active=True, referral_code="REF123")
    assert uf.role == "customer"
    assert uf.is_active is True
    assert uf.referral_code == "REF123"

    # CamelCase parsing
    uf_camel = UserFilter.model_validate({
        "role": "valet",
        "isOnDuty": True,
        "isSellerAdmin": False,
        "approvalStatus": "approved",
        "allowedIds": ["1", "2"]
    })
    assert uf_camel.is_on_duty is True
    assert uf_camel.is_seller_admin is False
    assert uf_camel.approval_status == "approved"
    assert uf_camel.allowed_ids == [1, 2]

    # Extra fields MUST be forbidden
    with pytest.raises(ValidationError):
        UserFilter.model_validate({"rogue_field": "disallowed"})


def test_user_dao_and_repository_strict_signatures():
    from app.db.mysql_user_dao import MySQLUserDAO
    from app.repositories.user_repository import UserRepository
    from app.models.user import UserFilter
    import inspect
    from typing import get_type_hints

    # MySQLUserDAO._build_query_conditions
    sig_build = inspect.signature(MySQLUserDAO._build_query_conditions)
    filter_param = sig_build.parameters["filter_params"]
    assert "Dict" not in str(filter_param.annotation), "Raw Dict found in _build_query_conditions annotation"
    assert "Union" not in str(filter_param.annotation), "Union found in _build_query_conditions annotation"

    # MySQLUserDAO.findOne
    sig_find_one = inspect.signature(MySQLUserDAO.findOne)
    param_find_one = sig_find_one.parameters["filter_params"]
    assert param_find_one.annotation == UserFilter, "MySQLUserDAO.findOne must strictly type filter_params to UserFilter"

    # UserRepository.findOne
    sig_repo_find_one = inspect.signature(UserRepository.findOne)
    repo_param = sig_repo_find_one.parameters["filter_params"]
    assert repo_param.annotation == UserFilter, "UserRepository.findOne must strictly type filter_params to UserFilter"


def test_section_1b_repository_typed_methods():
    from app.repositories.product_repository import product_repository
    from app.repositories.review_classification_repository import review_classification_repository
    from app.repositories.product_review_repository import product_review_repository
    from app.repositories.user_repository import user_repository

    assert hasattr(product_repository, "findByIds"), "product_repository must have findByIds"
    assert hasattr(review_classification_repository, "find_active"), "review_classification_repository must have find_active"
    assert hasattr(product_review_repository, "find_approved_by_product"), "product_review_repository must have find_approved_by_product"
    assert hasattr(user_repository, "findSuperAdmin"), "user_repository must have findSuperAdmin"
    assert hasattr(user_repository, "findByReferralCode"), "user_repository must have findByReferralCode"


def test_section_3_in_memory_pushdowns():
    from app.repositories.stock_reservation_repository import stock_reservation_repository
    from app.repositories.product_repository import product_repository
    from app.repositories.category_repository import category_repository
    import app.routers.products as products_router_mod
    import app.db.mysql_cart_dao as cart_dao_mod
    import app.db.mysql_wishlist_dao as wishlist_dao_mod
    import inspect
    import ast

    # 1. Methods exist
    assert hasattr(stock_reservation_repository, "get_reserved_quantities_bulk"), "stock_reservation_repository must have get_reserved_quantities_bulk"
    assert hasattr(product_repository, "findByName"), "product_repository must have findByName"
    assert hasattr(category_repository, "findByCategoryTag"), "category_repository must have findByCategoryTag"

    # 2. CartDAO.deleteMany AST has no for-loops (set-based pushdown)
    cart_source = inspect.getsource(cart_dao_mod.MySQLCartDAO.deleteMany)
    assert "for r in records" not in cart_source, "MySQLCartDAO.deleteMany must not loop over records in Python"

    # 3. WishlistDAO.deleteMany AST has no for-loops (set-based pushdown)
    wishlist_source = inspect.getsource(wishlist_dao_mod.MySQLWishlistDAO.deleteMany)
    assert "for wid in wids" not in wishlist_source, "MySQLWishlistDAO.deleteMany must not loop over wids in Python"

    # 4. products router create_product does not call findAll()
    create_prod_source = inspect.getsource(products_router_mod.create_product)
    assert "product_repository.findAll()" not in create_prod_source, "create_product must not call findAll() for duplicate checks"


def test_section_2a_models_extra_forbid():
    from app.models.commission_settings import CommissionSettings
    from app.models.daos_flat import ProductNotificationsInternal
    from app.models.division import DivisionCategoryTag, DivisionInternal, DivisionInternalCreate, DivisionInternalUpdate
    from app.models.schemas import AddressSnippet, TrackBeaconRequest, TrackNotifyPincodeRequest
    from app.routers.auth import RefreshTokenClaims
    from app.routers.tracking import BaseTrackingRequest

    models = [
        CommissionSettings,
        ProductNotificationsInternal,
        DivisionCategoryTag,
        DivisionInternal,
        DivisionInternalCreate,
        DivisionInternalUpdate,
        AddressSnippet,
        TrackBeaconRequest,
        TrackNotifyPincodeRequest,
        RefreshTokenClaims,
        BaseTrackingRequest,
    ]
    for m in models:
        assert m.model_config.get("extra") == "forbid", f"Model {m.__name__} must have extra='forbid', found {m.model_config.get('extra')}"


def test_section_2b_zero_reflection_in_repositories_and_routers():
    import app.repositories.coupon_repository as coupon_repo_mod
    import app.routers.orders as orders_router_mod
    import app.routers.returns as returns_router_mod
    import app.routers.bundles as bundles_router_mod
    import inspect

    coupon_src = inspect.getsource(coupon_repo_mod.CouponRepository.create)
    assert "getattr(" not in coupon_src, "CouponRepository.create must not use getattr"

    orders_src = inspect.getsource(orders_router_mod.update_order_status)
    assert "getattr(" not in orders_src, "orders router update_order_status must not use getattr"

    returns_src = inspect.getsource(returns_router_mod.populate_return_request)
    assert "getattr(" not in returns_src, "returns router populate_return_request must not use getattr"

    bundles_src = inspect.getsource(bundles_router_mod._enrich_bundle)
    assert "hasattr(" not in bundles_src, "bundles router _enrich_bundle must not use hasattr"


def test_user_and_sub_order_cleanups_integrity():
    import inspect
    from typing import Optional, List
    from app.models.user import User, UserFilter
    from app.models.schemas import UserInternalCreate, UserInternalUpdate, UserBase, UserUpdate, UserResponse
    from app.models.daos_flat import (
        DeviceSubscriptionInternal,
        DeviceSubscriptionInternalCreate,
        DeviceSubscriptionInternalUpdate,
    )
    from app.db.mysql_user_dao import MySQLUserDAO
    from app.db.mysql_sub_order_dao import MySQLSubOrderDAO
    from app.db.mysql_deviceSubscriptions_dao import MySQLDeviceSubscriptionsDAO
    from app.repositories.user_repository import UserRepository
    from app.repositories.sub_order_repository import SubOrderRepository
    from app.services.push_notification_service import PushNotificationService

    # 1. User.id & UserResponse.id are native int, no user_id field on User/UserResponse/UserInternalCreate/UserInternalUpdate
    u = User(id=42)
    assert u.id == 42
    assert UserResponse.model_fields["id"].annotation == int
    for model_cls in (User, UserResponse, UserInternalCreate, UserInternalUpdate):
        assert "user_id" not in model_cls.model_fields, f"user_id must not be a field on {model_cls.__name__}"
    assert not hasattr(u, "user_id"), "User must not have a redundant user_id property"

    # 2. DeviceSubscriptionInternal models & DAO use Optional[int] for user_id, and PushNotificationService uses typed attributes
    for ds_cls in (DeviceSubscriptionInternal, DeviceSubscriptionInternalCreate, DeviceSubscriptionInternalUpdate):
        assert ds_cls.model_fields["user_id"].annotation == Optional[int], f"{ds_cls.__name__}.user_id must be Optional[int]"
    assert inspect.signature(MySQLDeviceSubscriptionsDAO.findOne).parameters["user_id"].annotation == Optional[int]
    assert inspect.signature(MySQLDeviceSubscriptionsDAO.findAll).parameters["user_id"].annotation == Optional[int]
    from app.models.daos import OrderFilter
    assert OrderFilter.model_fields["user_ids"].annotation == Optional[List[str]], "OrderFilter.user_ids must strictly be Optional[List[str]] with no Union"
    push_src = inspect.getsource(PushNotificationService)
    assert 'notification["userSegment"]' not in push_src
    assert 'd["userId"]' not in push_src
    assert 'device["endpoint"]' not in push_src
    assert 'isinstance(device.keys' not in push_src, "PushNotificationService must not use isinstance on typed Pydantic device.keys"

    # 3. payment_terms is integer typed with no redundant int() casting and default 30 in UserRepository.create
    import re
    for model_cls in (User, UserBase, UserUpdate, UserResponse, UserInternalCreate, UserInternalUpdate):
        assert model_cls.model_fields["payment_terms"].annotation == Optional[int]
    dao_src = inspect.getsource(MySQLUserDAO)
    assert 'replace("net_"' not in dao_src, "MySQLUserDAO must not string-strip 'net_' from payment_terms"
    assert not re.search(r"\bint\(", dao_src), "MySQLUserDAO must have zero redundant int(...) casts"
    repo_create_src = inspect.getsource(UserRepository.create)
    assert 'else "30"' not in repo_create_src, "UserRepository.create must use integer 30 for payment_terms default"
    assert "getNextUserId" not in repo_create_src, "UserRepository.create must not call getNextUserId before DAO create"

    # 4. UserFilter.allowed_ids & MySQLUserDAO._fetch_children / _replace_children use typed AddressSnippet & native int zones
    assert UserFilter.model_fields["allowed_ids"].annotation == Optional[List[int]]
    build_cond_src = inspect.getsource(MySQLUserDAO._build_query_conditions)
    assert "try:" not in build_cond_src
    assert "isinstance(filter_params, dict)" not in build_cond_src
    fetch_children_src = inspect.getsource(MySQLUserDAO._fetch_children)
    assert "AddressSnippet(" in fetch_children_src, "_fetch_children must construct AddressSnippet instances directly"
    assert "r.zone_id" in fetch_children_src and "append(r.zone_name)" not in fetch_children_src, "_fetch_children must append r.zone_id (int)"
    replace_child_src = inspect.getsource(MySQLUserDAO._replace_children)
    assert "AddressSnippet.model_validate" not in replace_child_src, "_replace_children must use AddressSnippet attributes directly"

    # 5. UserRepository & SubOrderRepository / MySQLSubOrderDAO accept native int IDs
    assert inspect.signature(UserRepository.findById).parameters["id"].annotation == int
    assert inspect.signature(UserRepository.findByIds).parameters["ids"].annotation == List[int]
    assert inspect.signature(UserRepository.update).parameters["id"].annotation == int
    assert inspect.signature(UserRepository.delete).parameters["id"].annotation == int
    assert inspect.signature(MySQLSubOrderDAO.findByParentOrder).parameters["parent_order_id"].annotation == int
    assert inspect.signature(SubOrderRepository.findByParentOrder).parameters["parent_order_id"].annotation == int
    assert "parent_order_number" not in inspect.getsource(MySQLSubOrderDAO.findByParentOrder)
