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
    item = CartItemInternal(id="item-123", product=456, quantity=2)
    assert item.id == "item-123"
    assert item.product == 456
    assert item.quantity == 2
    assert not hasattr(item, "id_")

    with pytest.raises(ValidationError):
        CartItemInternal(product=456, _id="legacy-id")


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
    ret_create = ReturnRequestInternalCreate(id=1, order_id=1)
    assert ret_create.id == 1
    assert ret_create.order_id == 1

    ret_int = ReturnRequestInternal(id=2, order_id=2)
    assert ret_int.id == 2
    assert ret_int.order_id == 2


def test_customer_segment_and_notification_purged():
    seg = CustomerSegmentInternalCreate(id="seg-1", name="VIP", type="manual", userIds=["u1"])
    assert seg.id == "seg-1"

    notif_create = NotificationInternalCreate(
        id=1, user_id=1, type="order", title="Shipped", message="Your order shipped"
    )
    assert notif_create.id == 1

    notif = NotificationInternal(
        id=2, user_id=1, type="order", title="Delivered", message="Order delivered", is_read=False, is_acknowledged=False
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


def test_product_and_coupon_pydantic_refactor_integrity():
    import inspect
    from typing import Optional, List, Tuple
    from app.models.product import Product, ProductFilter, ProductCatalogQuery, ProductFacets
    from app.db.mysql_product_dao import MySQLProductDAO
    from app.repositories.product_repository import ProductRepository
    from app.repositories.coupon_repository import CouponRepository, OverlapConflictError
    from app.models.daos_flat import CouponOverlapData, CouponOverlapDetail

    # 1. ProductFilter & ProductCatalogQuery typing and pure integer ID
    assert ProductCatalogQuery is ProductFilter
    assert ProductFilter.model_fields["allowed_ids"].annotation == Optional[List[int]]
    assert ProductFilter.model_fields["id"].annotation == Optional[int]
    assert ProductFilter.model_fields["seller_ids"].annotation == Optional[List[int]]
    assert ProductFilter.model_fields["my_seller_id"].annotation == Optional[int]
    assert "product_id_formatted" not in ProductFilter.model_fields, "ProductFilter must not have legacy product_id_formatted"

    filt = ProductFilter(id=456)
    assert filt.id == 456

    # 2. MySQLProductDAO signatures and SQL condition builder integrity
    dao_cond_src = inspect.getsource(MySQLProductDAO._build_query_conditions)
    assert "productIdFormattedVal" not in dao_cond_src, "MySQLProductDAO must not use productIdFormattedVal"
    assert "str(sid)" not in dao_cond_src, "MySQLProductDAO must not string-cast sid"
    assert "int(num_id)" not in dao_cond_src, "MySQLProductDAO must not cast num_id in query builder"
    assert "int(pf)" not in dao_cond_src, "MySQLProductDAO must not cast pf in query builder"
    assert "[int(aid) for aid in allowed_ids]" not in dao_cond_src, "allowed_ids must already be List[int]"

    # deleteMany returns native int count
    assert inspect.signature(MySQLProductDAO.deleteMany).return_annotation == int
    # find_paginated accepts ProductFilter and returns tuple[List[Product], int]
    assert inspect.signature(MySQLProductDAO.find_paginated).parameters["filter"].annotation == ProductFilter
    assert inspect.signature(MySQLProductDAO.find_paginated).return_annotation == tuple[List[Product], int]
    # get_facets accepts ProductFilter and returns ProductFacets
    assert inspect.signature(MySQLProductDAO.get_facets).parameters["filter"].annotation == ProductFilter
    assert inspect.signature(MySQLProductDAO.get_facets).return_annotation == ProductFacets

    # 3. ProductRepository get_catalog contract
    get_cat_sig = inspect.signature(ProductRepository.get_catalog)
    assert get_cat_sig.parameters["filter"].annotation == ProductFilter
    assert get_cat_sig.return_annotation == Tuple[List[Product], int, ProductFacets, bool, Optional[str]]
    get_cat_src = inspect.getsource(ProductRepository.get_catalog)
    assert "query.copy()" not in get_cat_src
    assert 'query["' not in get_cat_src
    assert "Union[" not in get_cat_src

    # 4. CouponRepository overlap & user behavior caching integrity
    check_overlap_sig = inspect.signature(CouponRepository.check_discount_overlap)
    assert check_overlap_sig.return_annotation == Optional[CouponOverlapData]
    overlap_src = inspect.getsource(CouponRepository.check_discount_overlap)
    assert "set().union(" not in overlap_src, "No star unpacking in check_discount_overlap"
    assert "user_behavior_cache" not in inspect.signature(CouponRepository.get_applicable_discounts_for_product).parameters
    assert "user_behavior_cache" not in inspect.signature(CouponRepository._user_matches_behavior).parameters

    coupon_repo_src = inspect.getsource(CouponRepository)
    assert "_user_behavior_cache" not in coupon_repo_src, "CouponRepository must not have internal _user_behavior_cache dict"
    assert "_categories_map" not in coupon_repo_src, "CouponRepository must not have in-memory _categories_map dict"
    assert "_brands_map" not in coupon_repo_src, "CouponRepository must not have in-memory _brands_map dict"
    assert "_collections_map" not in coupon_repo_src, "CouponRepository must not have in-memory _collections_map dict"
    assert "str(c.id) == str(default_auto_discount.id)" not in coupon_repo_src, "Must compare c.id == default_auto_discount.id directly"
    assert "str(user_id).isdigit()" not in coupon_repo_src, "No defensive isdigit checks on user_id"
    assert "uid = int(user_id)" not in coupon_repo_src, "No defensive uid assignment"
    assert "segment.user_ids" not in coupon_repo_src, "Must not scan segment.user_ids in memory"
    assert "customer_segments_repository.has_user" in coupon_repo_src, "Must delegate to customer_segments_repository.has_user"

    # 5. CustomerSegmentsRepository & MySQLCustomerSegmentDAO has_user relational pushdown
    from app.repositories.customer_segments_repository import CustomerSegmentsRepository
    from app.db.mysql_customer_segment_dao import MySQLCustomerSegmentDAO

    assert inspect.signature(CustomerSegmentsRepository.has_user).parameters["segment_id"].annotation == int
    assert inspect.signature(CustomerSegmentsRepository.has_user).parameters["user_id"].annotation == int
    assert inspect.signature(MySQLCustomerSegmentDAO.has_user).parameters["segment_id"].annotation == int
    assert inspect.signature(MySQLCustomerSegmentDAO.has_user).parameters["user_id"].annotation == int
    dao_has_user_src = inspect.getsource(MySQLCustomerSegmentDAO.has_user)
    assert "SELECT 1 FROM sj_customer_segment_users" in dao_has_user_src
    assert "LIMIT 1" in dao_has_user_src
    assert "str(" not in dao_has_user_src, "has_user must not string-cast segment_id or user_id"


@pytest.mark.asyncio
async def test_coupon_user_matches_segment_behavior_relational():
    from unittest.mock import AsyncMock
    from app.repositories.coupon_repository import coupon_repository
    from app.repositories.customer_segments_repository import customer_segments_repository

    orig_has_user = customer_segments_repository.has_user
    try:
        customer_segments_repository.has_user = AsyncMock(side_effect=lambda seg_id, uid: seg_id == 5 and uid == 100)

        # Matched segment
        matched = await coupon_repository._user_matches_behavior(100, "segment_5")
        assert matched is True

        # Unmatched segment
        unmatched = await coupon_repository._user_matches_behavior(200, "segment_5")
        assert unmatched is False
    finally:
        customer_segments_repository.has_user = orig_has_user


@pytest.mark.asyncio
async def test_analytics_batch_5_methods_model_integrity():
    import inspect
    from typing import List, Optional
    from unittest.mock import AsyncMock
    from app.repositories.analytics_repository import analytics_repository
    from app.models.analytics_schemas import (
        SalesOverTimeResponse,
        AverageOrderValueResponse,
        SalesByChannelResponse,
        SalesByProductResponse,
    )
    from app.models.schemas import ProductSellerEntry
    from app.models.order import Order, OrderItem
    from app.models.product import Product

    # Check method signatures and annotations
    for method_name, expected_return in [
        ("get_sales_over_time", List[SalesOverTimeResponse]),
        ("get_average_order_value_over_time", List[AverageOrderValueResponse]),
        ("get_sales_by_channel", List[SalesByChannelResponse]),
        ("get_sales_by_product", List[SalesByProductResponse]),
    ]:
        fn = getattr(analytics_repository, method_name)
        sig = inspect.signature(fn)
        assert sig.return_annotation == expected_return, f"{method_name} return must be {expected_return}"
        assert sig.parameters["seller_id"].annotation == Optional[int], f"{method_name} seller_id must be Optional[int]"

    # Test runtime execution with mock data
    mock_order = Order(
        id=1,
        total=150.0,
        channel="mobile_web",
        seller_id=10,
        created_at="2026-03-15T10:00:00",
        items=[
            OrderItem(
                product_id=50,
                name="Notebook",
                price=50.0,
                quantity=3,
            )
        ],
    )
    mock_product = Product(
        id=50,
        product_id=50,
        name="Notebook",
        price=50.0,
        stock=100,
        sellers=[ProductSellerEntry(seller_id=10, request_status="approved")],
    )

    orig_sot = getattr(analytics_repository.order_storage, "get_sales_over_time_stats", None)
    orig_aov = getattr(analytics_repository.order_storage, "get_average_order_value_over_time_stats", None)
    orig_sbc = getattr(analytics_repository.order_storage, "get_sales_by_channel_stats", None)
    orig_sbp = getattr(analytics_repository.order_storage, "get_sales_by_product_stats", None)
    try:
        analytics_repository.order_storage.get_sales_over_time_stats = AsyncMock(
            return_value=[SalesOverTimeResponse(period="2026-03-15", sales=150.0, orderCount=1, aov=150.0)]
        )
        analytics_repository.order_storage.get_average_order_value_over_time_stats = AsyncMock(
            return_value=[AverageOrderValueResponse(period="2026-03-15", average_order_value=150.0)]
        )
        analytics_repository.order_storage.get_sales_by_channel_stats = AsyncMock(
            return_value=[
                SalesByChannelResponse(channel="mobile_web", sales=150.0),
                SalesByChannelResponse(channel="desktop_web", sales=0.0),
                SalesByChannelResponse(channel="mobile_app", sales=0.0),
            ]
        )
        analytics_repository.order_storage.get_sales_by_product_stats = AsyncMock(
            return_value=[SalesByProductResponse(productId=50, name="Notebook", quantity=3, revenue=150.0)]
        )

        # 1. get_sales_over_time
        res_sot = await analytics_repository.get_sales_over_time(group_by="day", seller_id=10)
        assert len(res_sot) == 1
        assert isinstance(res_sot[0], SalesOverTimeResponse)
        assert res_sot[0].sales == 150.0
        assert res_sot[0].orderCount == 1
        assert res_sot[0].aov == 150.0

        # 2. get_average_order_value_over_time
        res_aov = await analytics_repository.get_average_order_value_over_time(group_by="day", seller_id=10)
        assert len(res_aov) == 1
        assert isinstance(res_aov[0], AverageOrderValueResponse)
        assert res_aov[0].average_order_value == 150.0

        # 3. get_sales_by_channel
        res_sbc = await analytics_repository.get_sales_by_channel(seller_id=10)
        assert len(res_sbc) >= 3
        assert all(isinstance(r, SalesByChannelResponse) for r in res_sbc)
        mobile_web = next(r for r in res_sbc if r.channel == "mobile_web")
        assert mobile_web.sales == 150.0

        # 4. get_sales_by_product
        res_sbp = await analytics_repository.get_sales_by_product(seller_id=10)
        assert len(res_sbp) == 1
        assert isinstance(res_sbp[0], SalesByProductResponse)
        assert res_sbp[0].product_id == 50
        assert res_sbp[0].name == "Notebook"
        assert res_sbp[0].quantity == 3
        assert res_sbp[0].revenue == 150.0
    finally:
        analytics_repository.order_storage.get_sales_over_time_stats = orig_sot
        analytics_repository.order_storage.get_average_order_value_over_time_stats = orig_aov
        analytics_repository.order_storage.get_sales_by_channel_stats = orig_sbc
        analytics_repository.order_storage.get_sales_by_product_stats = orig_sbp


@pytest.mark.asyncio
async def test_analytics_batch_6_methods_model_integrity():
    from app.repositories.analytics_repository import analytics_repository
    from app.db.mysql_order_dao import MySQLOrderDAO
    from app.models.analytics_schemas import (
        ReturnsReportResponse,
        PaymentMethodsReportResponse,
        RevenueByCategoryResponse,
        FulfillmentTimeReportResponse,
    )
    from app.models.order import Order
    from app.models.product import Product
    from app.models.user import User
    from app.models.schemas import ItemSnippet as OrderItem, ProductSellerEntry
    from app.models.daos import ReturnRequestInternal
    from app.models.schemas import ReturnItemSchema
    import inspect
    from typing import Optional, List
    from unittest.mock import AsyncMock
    from datetime import datetime

    # 1. Verify signatures and return annotations on analytics_repository
    for method_name, expected_return in [
        ("get_returns_report", List[ReturnsReportResponse]),
        ("get_payment_methods_report", List[PaymentMethodsReportResponse]),
        ("get_revenue_by_category", List[RevenueByCategoryResponse]),
        ("get_fulfillment_time_report", List[FulfillmentTimeReportResponse]),
    ]:
        fn = getattr(analytics_repository, method_name)
        sig = inspect.signature(fn)
        assert sig.return_annotation == expected_return, f"{method_name} return must be {expected_return}"
        assert sig.parameters["seller_id"].annotation == Optional[int], f"{method_name} seller_id must be Optional[int]"

    # 2. Verify signatures in MySQLOrderDAO
    for dao_method in [
        "get_returns_report_stats",
        "get_payment_methods_report_stats",
        "get_revenue_by_category_stats",
        "get_fulfillment_time_report_stats",
    ]:
        fn = getattr(MySQLOrderDAO, dao_method)
        sig = inspect.signature(fn)
        assert sig.parameters["seller_id"].annotation == Optional[int], f"{dao_method} seller_id must be Optional[int]"

    # 3. Test runtime execution with mock data
    mock_order = Order(
        id=101,
        order_number="ORD-101",
        user=5,
        total=250.0,
        status="delivered",
        seller_id=10,
        payment_method="card",
        created_at="2026-03-15T10:00:00",
        updated_at="2026-03-15T14:00:00",
        items=[
            OrderItem(
                product_id=50,
                name="Notebook",
                price=50.0,
                quantity=5,
                subtotal=250.0,
            )
        ],
    )
    mock_product = Product(
        id=50,
        product_id=50,
        name="Notebook",
        price=50.0,
        stock=100,
        category="Stationery",
        sellers=[ProductSellerEntry(seller_id=10, request_status="approved")],
    )
    mock_user = User(
        id=5,
        name="Alice Smith",
        email="alice@example.com",
        role="customer",
    )
    mock_return = ReturnRequestInternal(
        id=1,
        return_id="RET-001",
        order_id=101,
        user_id=5,
        status="approved",
        payment_method="card",
        created_at=datetime(2026, 3, 16, 12, 0, 0),
        items=[
            ReturnItemSchema(
                product_id=50,
                quantity=1,
                reason="Defective",
            )
        ],
    )

    orig_ret = getattr(analytics_repository.order_storage, "get_returns_report_stats", None)
    orig_pm = getattr(analytics_repository.order_storage, "get_payment_methods_report_stats", None)
    orig_cat = getattr(analytics_repository.order_storage, "get_revenue_by_category_stats", None)
    orig_ft = getattr(analytics_repository.order_storage, "get_fulfillment_time_report_stats", None)

    try:
        analytics_repository.order_storage.get_returns_report_stats = AsyncMock(
            return_value=[
                ReturnsReportResponse(
                    returnId="RET-001",
                    orderId=101,
                    userName="Alice Smith",
                    userEmail="alice@example.com",
                    itemCount=1,
                    paymentMethod="card",
                    refundValue=50.0,
                    status="approved",
                    createdAt=datetime(2026, 3, 16, 12, 0, 0),
                )
            ]
        )
        analytics_repository.order_storage.get_payment_methods_report_stats = AsyncMock(
            return_value=[
                PaymentMethodsReportResponse(
                    paymentMethod="card",
                    orderCount=1,
                    revenue=250.0,
                    avgOrderValue=250.0,
                )
            ]
        )
        analytics_repository.order_storage.get_revenue_by_category_stats = AsyncMock(
            return_value=[
                RevenueByCategoryResponse(
                    category="Stationery",
                    orderCount=1,
                    quantity=5,
                    revenue=250.0,
                )
            ]
        )
        analytics_repository.order_storage.get_fulfillment_time_report_stats = AsyncMock(
            return_value=[
                FulfillmentTimeReportResponse(
                    orderId=101,
                    orderNumber="ORD-101",
                    userName="Alice Smith",
                    status="delivered",
                    fulfillmentHours=4.0,
                    orderTotal=250.0,
                    createdAt=datetime(2026, 3, 15, 10, 0, 0),
                )
            ]
        )

        # 1. get_returns_report
        res_ret = await analytics_repository.get_returns_report(seller_id=10)
        assert len(res_ret) == 1
        assert isinstance(res_ret[0], ReturnsReportResponse)
        assert res_ret[0].returnId == "RET-001"
        assert res_ret[0].orderId == 101
        assert res_ret[0].userName == "Alice Smith"
        assert res_ret[0].itemCount == 1
        assert res_ret[0].paymentMethod == "card"
        assert res_ret[0].createdAt == datetime(2026, 3, 16, 12, 0, 0)

        # 2. get_payment_methods_report
        res_pm = await analytics_repository.get_payment_methods_report(seller_id=10)
        assert len(res_pm) == 1
        assert isinstance(res_pm[0], PaymentMethodsReportResponse)
        assert res_pm[0].paymentMethod == "card"
        assert res_pm[0].orderCount == 1
        assert res_pm[0].revenue == 250.0
        assert res_pm[0].avgOrderValue == 250.0

        # 3. get_revenue_by_category
        res_cat = await analytics_repository.get_revenue_by_category(seller_id=10)
        assert len(res_cat) == 1
        assert isinstance(res_cat[0], RevenueByCategoryResponse)
        assert res_cat[0].category == "Stationery"
        assert res_cat[0].orderCount == 1
        assert res_cat[0].quantity == 5
        assert res_cat[0].revenue == 250.0

        # 4. get_fulfillment_time_report
        res_ft = await analytics_repository.get_fulfillment_time_report(seller_id=10)
        assert len(res_ft) == 1
        assert isinstance(res_ft[0], FulfillmentTimeReportResponse)
        assert res_ft[0].orderId == 101
        assert res_ft[0].orderNumber == "ORD-101"
        assert res_ft[0].userName == "Alice Smith"
        assert res_ft[0].fulfillmentHours == 4.0
        assert res_ft[0].orderTotal == 250.0
        assert res_ft[0].createdAt == datetime(2026, 3, 15, 10, 0, 0)
    finally:
        analytics_repository.order_storage.get_returns_report_stats = orig_ret
        analytics_repository.order_storage.get_payment_methods_report_stats = orig_pm
        analytics_repository.order_storage.get_revenue_by_category_stats = orig_cat
        analytics_repository.order_storage.get_fulfillment_time_report_stats = orig_ft



