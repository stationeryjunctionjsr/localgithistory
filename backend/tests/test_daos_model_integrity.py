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


@pytest.mark.asyncio
async def test_analytics_repository_next_10_methods_model_integrity():
    from app.repositories.analytics_repository import analytics_repository
    from app.db.mysql_order_dao import MySQLOrderDAO
    from app.models.analytics_schemas import (
        CouponUsageReportResponse,
        SalesByLocationReportResponse,
        NewVsReturningCustomerSalesResponse,
        ItemsBoughtTogetherResponse,
        SalesByDeviceReportResponse,
        SearchesNoClicksResponse,
        SearchConversionResponse,
        BounceRateResponse,
        SessionsOverTimeResponse,
        SessionsByDeviceResponse,
    )
    from app.models.tracking import Tracking
    from app.models.session import Session
    from app.models.daos import DeviceSnippet
    import inspect
    from typing import Optional, List
    from unittest.mock import AsyncMock

    # 1. Verify signatures and return annotations on analytics_repository
    expected_sigs = [
        ("get_coupon_usage_report", List[CouponUsageReportResponse]),
        ("get_sales_by_location", List[SalesByLocationReportResponse]),
        ("get_new_vs_returning_customer_sales", List[NewVsReturningCustomerSalesResponse]),
        ("get_items_bought_together", List[ItemsBoughtTogetherResponse]),
        ("get_sales_by_device_type", List[SalesByDeviceReportResponse]),
        ("get_searches_with_no_clicks", List[SearchesNoClicksResponse]),
        ("get_search_conversion_rate", List[SearchConversionResponse]),
        ("get_bounce_rate_over_time", List[BounceRateResponse]),
        ("get_sessions_over_time", List[SessionsOverTimeResponse]),
        ("get_sessions_by_device_type", List[SessionsByDeviceResponse]),
    ]
    for method_name, expected_return in expected_sigs:
        fn = getattr(analytics_repository, method_name)
        sig = inspect.signature(fn)
        assert sig.return_annotation == expected_return, f"{method_name} return must be {expected_return}"

    # 2. Verify seller_id is Optional[int]
    for method_name in [
        "get_coupon_usage_report",
        "get_sales_by_location",
        "get_searches_with_no_clicks",
        "get_search_conversion_rate",
        "get_bounce_rate_over_time",
        "get_sessions_over_time",
    ]:
        fn = getattr(analytics_repository, method_name)
        sig = inspect.signature(fn)
        assert sig.parameters["seller_id"].annotation == Optional[int], f"{method_name} seller_id must be Optional[int]"

    # 3. Verify DAO signatures
    from app.db.mysql_tracking_dao import MySQLTrackingDAO
    from app.db.mysql_session_dao import MySQLSessionDAO

    for dao_method in ["get_coupon_usage_report_stats", "get_sales_by_location_stats"]:
        fn = getattr(MySQLOrderDAO, dao_method)
        sig = inspect.signature(fn)
        assert sig.parameters["seller_id"].annotation == Optional[int], f"{dao_method} seller_id must be Optional[int]"

    for dao_method in [
        "get_searches_with_no_clicks_stats",
        "get_search_conversion_rate_stats",
        "get_bounce_rate_over_time_stats",
        "get_sessions_over_time_stats",
    ]:
        fn = getattr(MySQLTrackingDAO, dao_method)
        sig = inspect.signature(fn)
        assert sig.parameters["seller_id"].annotation == Optional[int], f"{dao_method} seller_id must be Optional[int]"

    fn_sbd = getattr(MySQLSessionDAO, "get_sessions_by_device_type_stats")
    sig_sbd = inspect.signature(fn_sbd)
    assert sig_sbd.return_annotation == List[SessionsByDeviceResponse]

    # 4. Verify ItemsBoughtTogetherResponse IDs are native int
    assert ItemsBoughtTogetherResponse.model_fields["productAId"].annotation is int
    assert ItemsBoughtTogetherResponse.model_fields["productBId"].annotation is int

    # 5. Test runtime execution of Methods 1-5 (Order DAO pushdowns)
    orig_coupon = getattr(analytics_repository.order_storage, "get_coupon_usage_report_stats", None)
    orig_loc = getattr(analytics_repository.order_storage, "get_sales_by_location_stats", None)
    orig_nvr = getattr(analytics_repository.order_storage, "get_new_vs_returning_customer_stats", None)
    orig_ibt = getattr(analytics_repository.order_storage, "get_items_bought_together_stats", None)
    orig_sbd = getattr(analytics_repository.order_storage, "get_sales_by_device_type_stats", None)

    try:
        analytics_repository.order_storage.get_coupon_usage_report_stats = AsyncMock(
            return_value=[
                CouponUsageReportResponse(
                    couponCode="WELCOME10",
                    discountType="percentage",
                    discountValue=10.0,
                    usageCount=5,
                    totalDiscountGiven=50.0,
                    totalRevenue=450.0,
                )
            ]
        )
        analytics_repository.order_storage.get_sales_by_location_stats = AsyncMock(
            return_value=[
                SalesByLocationReportResponse(
                    location="Jamshedpur, Jharkhand",
                    orderCount=10,
                    quantity=25,
                    revenue=2500.0,
                )
            ]
        )
        analytics_repository.order_storage.get_new_vs_returning_customer_stats = AsyncMock(
            return_value=[
                NewVsReturningCustomerSalesResponse(
                    customerType="New Customers",
                    orderCount=7,
                    revenue=1500.0,
                )
            ]
        )
        analytics_repository.order_storage.get_items_bought_together_stats = AsyncMock(
            return_value=[
                ItemsBoughtTogetherResponse(
                    productAId=10,
                    productAName="Notebook",
                    productBId=20,
                    productBName="Gel Pen",
                    frequency=8,
                )
            ]
        )
        analytics_repository.order_storage.get_sales_by_device_type_stats = AsyncMock(
            return_value=[
                SalesByDeviceReportResponse(
                    deviceType="mobile",
                    orderCount=12,
                    revenue=3000.0,
                )
            ]
        )

        # Execute Methods 1-5
        res_coupon = await analytics_repository.get_coupon_usage_report(seller_id=10)
        assert len(res_coupon) == 1
        assert isinstance(res_coupon[0], CouponUsageReportResponse)
        assert res_coupon[0].couponCode == "WELCOME10"

        res_loc = await analytics_repository.get_sales_by_location(limit=10, seller_id=10)
        assert len(res_loc) == 1
        assert isinstance(res_loc[0], SalesByLocationReportResponse)
        assert res_loc[0].location == "Jamshedpur, Jharkhand"

        res_nvr = await analytics_repository.get_new_vs_returning_customer_sales()
        assert len(res_nvr) == 1
        assert isinstance(res_nvr[0], NewVsReturningCustomerSalesResponse)
        assert res_nvr[0].customerType == "New Customers"

        res_ibt = await analytics_repository.get_items_bought_together(limit=5)
        assert len(res_ibt) == 1
        assert isinstance(res_ibt[0], ItemsBoughtTogetherResponse)
        assert res_ibt[0].productAId == 10
        assert isinstance(res_ibt[0].productAId, int)
        assert res_ibt[0].productBId == 20
        assert isinstance(res_ibt[0].productBId, int)

        res_sbd = await analytics_repository.get_sales_by_device_type()
        assert len(res_sbd) == 1
        assert isinstance(res_sbd[0], SalesByDeviceReportResponse)
        assert res_sbd[0].deviceType == "mobile"

    finally:
        analytics_repository.order_storage.get_coupon_usage_report_stats = orig_coupon
        analytics_repository.order_storage.get_sales_by_location_stats = orig_loc
        analytics_repository.order_storage.get_new_vs_returning_customer_stats = orig_nvr
        analytics_repository.order_storage.get_items_bought_together_stats = orig_ibt
        analytics_repository.order_storage.get_sales_by_device_type_stats = orig_sbd

    # 6. Test runtime execution of Methods 6-10 (Tracking and session pushdowns)
    orig_snc = getattr(analytics_repository.tracking_storage, "get_searches_with_no_clicks_stats", None)
    orig_scr = getattr(analytics_repository.tracking_storage, "get_search_conversion_rate_stats", None)
    orig_br = getattr(analytics_repository.tracking_storage, "get_bounce_rate_over_time_stats", None)
    orig_sot = getattr(analytics_repository.tracking_storage, "get_sessions_over_time_stats", None)
    orig_dev = getattr(analytics_repository.session_storage, "get_sessions_by_device_type_stats", None)

    try:
        analytics_repository.tracking_storage.get_searches_with_no_clicks_stats = AsyncMock(
            return_value=[
                SearchesNoClicksResponse(
                    term="gel pen",
                    searchCount=2,
                    totalResults=8,
                    avgResults=4.0,
                )
            ]
        )
        analytics_repository.tracking_storage.get_search_conversion_rate_stats = AsyncMock(
            return_value=[
                SearchConversionResponse(
                    totalSearchSessions=3,
                    convertedSessions=1,
                    nonConvertedSessions=2,
                    conversionRate=33.33,
                )
            ]
        )
        analytics_repository.tracking_storage.get_bounce_rate_over_time_stats = AsyncMock(
            return_value=[
                BounceRateResponse(
                    period="2026-03-15",
                    totalSessions=2,
                    bouncedSessions=1,
                    bounceRate=50.0,
                )
            ]
        )
        analytics_repository.tracking_storage.get_sessions_over_time_stats = AsyncMock(
            return_value=[
                SessionsOverTimeResponse(
                    period="2026-03-15",
                    sessions=3,
                    visitors=2,
                    uniqueVisitors=2,
                )
            ]
        )
        analytics_repository.session_storage.get_sessions_by_device_type_stats = AsyncMock(
            return_value=[
                SessionsByDeviceResponse(device="desktop", sessions=2),
                SessionsByDeviceResponse(device="mobile", sessions=2),
            ]
        )

        res_snc = await analytics_repository.get_searches_with_no_clicks()
        assert len(res_snc) == 1
        assert isinstance(res_snc[0], SearchesNoClicksResponse)
        assert res_snc[0].term == "gel pen"

        res_scr = await analytics_repository.get_search_conversion_rate()
        assert len(res_scr) == 1
        assert isinstance(res_scr[0], SearchConversionResponse)
        assert res_scr[0].totalSearchSessions == 3

        res_br = await analytics_repository.get_bounce_rate_over_time()
        assert len(res_br) == 1
        assert isinstance(res_br[0], BounceRateResponse)
        assert res_br[0].period == "2026-03-15"

        res_sot = await analytics_repository.get_sessions_over_time()
        assert len(res_sot) == 1
        assert isinstance(res_sot[0], SessionsOverTimeResponse)
        assert res_sot[0].period == "2026-03-15"

        res_dev = await analytics_repository.get_sessions_by_device_type()
        assert len(res_dev) == 2
        assert isinstance(res_dev[0], SessionsByDeviceResponse)
        assert res_dev[0].device == "desktop"

    finally:
        analytics_repository.tracking_storage.get_searches_with_no_clicks_stats = orig_snc
        analytics_repository.tracking_storage.get_search_conversion_rate_stats = orig_scr
        analytics_repository.tracking_storage.get_bounce_rate_over_time_stats = orig_br
        analytics_repository.tracking_storage.get_sessions_over_time_stats = orig_sot
        analytics_repository.session_storage.get_sessions_by_device_type_stats = orig_dev


@pytest.mark.asyncio
async def test_tracking_and_session_pushdown_dao_methods():
    from unittest.mock import patch, MagicMock, AsyncMock
    from datetime import datetime, timezone
    from app.db.mysql_tracking_dao import MySQLTrackingDAO
    from app.db.mysql_session_dao import MySQLSessionDAO
    from app.models.analytics_schemas import (
        SearchesNoClicksResponse,
        SearchConversionResponse,
        BounceRateResponse,
        SessionsOverTimeResponse,
        SessionsByDeviceResponse,
    )

    # 1. Test MySQLTrackingDAO.get_searches_with_no_clicks_stats
    dao_track = MySQLTrackingDAO()
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    row_snc = MagicMock()
    row_snc.term = "fountain pen"
    row_snc.search_count = 5
    row_snc.total_results = 20
    row_snc.avg_results = 4.0
    mock_res_snc = MagicMock()
    mock_res_snc.fetchall.return_value = [row_snc]
    mock_session.execute.return_value = mock_res_snc

    start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    end = datetime(2026, 3, 31, tzinfo=timezone.utc)

    with patch("app.db.mysql_tracking_dao.get_async_session_factory", return_value=mock_factory):
        res = await dao_track.get_searches_with_no_clicks_stats(start_date=start, end_date=end, seller_id=10)
        assert len(res) == 1
        assert isinstance(res[0], SearchesNoClicksResponse)
        assert res[0].term == "fountain pen"
        assert res[0].searchCount == 5
        assert res[0].totalResults == 20
        assert res[0].avgResults == 4.0
        query_snc = str(mock_session.execute.call_args[0][0])
        assert "GROUP BY LOWER(TRIM(t.search_term))" in query_snc
        assert "NOT EXISTS" in query_snc

    # 2. Test MySQLTrackingDAO.get_search_conversion_rate_stats
    row_scr = MagicMock()
    row_scr.total_search_sessions = 10
    row_scr.converted_sessions = 3
    row_scr.non_converted_sessions = 7
    row_scr.conversion_rate = 30.0
    mock_res_scr = MagicMock()
    mock_res_scr.fetchone.return_value = row_scr
    mock_session.execute.return_value = mock_res_scr

    with patch("app.db.mysql_tracking_dao.get_async_session_factory", return_value=mock_factory):
        res = await dao_track.get_search_conversion_rate_stats(start_date=start, end_date=end, seller_id=10)
        assert len(res) == 1
        assert isinstance(res[0], SearchConversionResponse)
        assert res[0].totalSearchSessions == 10
        assert res[0].convertedSessions == 3
        assert res[0].nonConvertedSessions == 7
        assert res[0].conversionRate == 30.0
        query_scr = str(mock_session.execute.call_args[0][0])
        assert "WITH search_sessions AS" in query_scr
        assert "LEFT JOIN order_sessions" in query_scr

    # 3. Test MySQLTrackingDAO.get_bounce_rate_over_time_stats
    row_br = MagicMock()
    row_br.period = "2026-03-15"
    row_br.total_sessions = 10
    row_br.bounced_sessions = 4
    row_br.bounce_rate = 40.0
    mock_res_br = MagicMock()
    mock_res_br.fetchall.return_value = [row_br]
    mock_session.execute.return_value = mock_res_br

    with patch("app.db.mysql_tracking_dao.get_async_session_factory", return_value=mock_factory):
        res = await dao_track.get_bounce_rate_over_time_stats(start_date=start, end_date=end, seller_id=10)
        assert len(res) == 1
        assert isinstance(res[0], BounceRateResponse)
        assert res[0].period == "2026-03-15"
        assert res[0].totalSessions == 10
        assert res[0].bouncedSessions == 4
        assert res[0].bounceRate == 40.0
        query_br = str(mock_session.execute.call_args[0][0])
        assert "WITH session_daily_views AS" in query_br
        assert "pv_count <= 1" in query_br

    # 4. Test MySQLTrackingDAO.get_sessions_over_time_stats
    row_sot = MagicMock()
    row_sot.period = "2026-03-15"
    row_sot.sessions = 25
    row_sot.visitors = 18
    row_sot.unique_visitors = 18
    mock_res_sot = MagicMock()
    mock_res_sot.fetchall.return_value = [row_sot]
    mock_session.execute.return_value = mock_res_sot

    with patch("app.db.mysql_tracking_dao.get_async_session_factory", return_value=mock_factory):
        res = await dao_track.get_sessions_over_time_stats(start_date=start, end_date=end, seller_id=10)
        assert len(res) == 1
        assert isinstance(res[0], SessionsOverTimeResponse)
        assert res[0].period == "2026-03-15"
        assert res[0].sessions == 25
        assert res[0].visitors == 18
        assert res[0].uniqueVisitors == 18
        query_sot = str(mock_session.execute.call_args[0][0])
        assert "DATE_FORMAT(event_timestamp, '%Y-%m-%d')" in query_sot
        assert "COUNT(DISTINCT COALESCE(user_id, session_id))" in query_sot

    # 5. Test MySQLSessionDAO.get_sessions_by_device_type_stats
    dao_session = MySQLSessionDAO()
    mock_session_s = AsyncMock()
    mock_factory_s = MagicMock()
    mock_factory_s.return_value.__aenter__.return_value = mock_session_s

    row_s1 = MagicMock()
    row_s1.device = "mobile"
    row_s1.sessions = 15
    row_s2 = MagicMock()
    row_s2.device = "desktop"
    row_s2.sessions = 10
    mock_res_sbd = MagicMock()
    mock_res_sbd.fetchall.return_value = [row_s1, row_s2]
    mock_session_s.execute.return_value = mock_res_sbd

    with patch("app.db.mysql_session_dao.get_async_session_factory", return_value=mock_factory_s):
        res = await dao_session.get_sessions_by_device_type_stats(start_date=start, end_date=end)
        assert len(res) == 2
        assert isinstance(res[0], SessionsByDeviceResponse)
        assert res[0].device == "mobile"
        assert res[0].sessions == 15
        assert res[1].device == "desktop"
        assert res[1].sessions == 10
        query_sbd = str(mock_session_s.execute.call_args[0][0])
        assert "FROM sj_analytics_sessions" in query_sbd
        assert "GROUP BY device" in query_sbd


@pytest.mark.asyncio
async def test_user_and_cohort_order_dao_pushdowns():
    from unittest.mock import patch, MagicMock, AsyncMock
    from datetime import datetime, timezone
    from typing import List
    from app.repositories.analytics_repository import analytics_repository
    from app.db.mysql_order_dao import MySQLOrderDAO
    from app.models.analytics_schemas import (
        CustomerCohortResponse,
        TopUsersReportResponse,
        UserOrderStatsResponse,
    )

    # 1. Verify signatures on analytics_repository
    assert inspect.signature(analytics_repository.get_customer_cohort_analysis).return_annotation == List[CustomerCohortResponse]
    assert inspect.signature(analytics_repository.get_top_users_by_revenue).return_annotation == List[TopUsersReportResponse]
    assert inspect.signature(analytics_repository.get_user_order_stats).return_annotation == List[UserOrderStatsResponse]

    # 2. Verify userId is native int
    assert TopUsersReportResponse.model_fields["userId"].annotation is int
    assert UserOrderStatsResponse.model_fields["userId"].annotation is int

    # 3. Verify repository delegation
    orig_cohort = getattr(analytics_repository.order_storage, "get_customer_cohort_stats", None)
    orig_top = getattr(analytics_repository.order_storage, "get_top_users_by_revenue_stats", None)
    orig_user = getattr(analytics_repository.order_storage, "get_user_order_stats_report", None)

    try:
        analytics_repository.order_storage.get_customer_cohort_stats = AsyncMock(
            return_value=[CustomerCohortResponse(cohort="2026-01", months=[10, 5, 2])]
        )
        analytics_repository.order_storage.get_top_users_by_revenue_stats = AsyncMock(
            return_value=[
                TopUsersReportResponse(
                    userId=101,
                    name="Alice",
                    userName="Alice",
                    email="alice@example.com",
                    userEmail="alice@example.com",
                    role="customer",
                    revenue=500.0,
                    orderCount=3,
                )
            ]
        )
        analytics_repository.order_storage.get_user_order_stats_report = AsyncMock(
            return_value=[
                UserOrderStatsResponse(
                    userId=101,
                    name="Alice",
                    email="alice@example.com",
                    totalOrders=3,
                    averageOrderValue=166.67,
                    daysSinceLastOrder=5,
                    avgOrdersPerMonth=1.5,
                )
            ]
        )

        res_c = await analytics_repository.get_customer_cohort_analysis()
        assert len(res_c) == 1
        assert res_c[0].cohort == "2026-01"
        assert res_c[0].months == [10, 5, 2]

        res_t = await analytics_repository.get_top_users_by_revenue()
        assert len(res_t) == 1
        assert res_t[0].userId == 101
        assert isinstance(res_t[0].userId, int)
        assert res_t[0].revenue == 500.0

        res_u = await analytics_repository.get_user_order_stats()
        assert len(res_u) == 1
        assert res_u[0].userId == 101
        assert isinstance(res_u[0].userId, int)
        assert res_u[0].totalOrders == 3
        assert res_u[0].averageOrderValue == 166.67
    finally:
        analytics_repository.order_storage.get_customer_cohort_stats = orig_cohort
        analytics_repository.order_storage.get_top_users_by_revenue_stats = orig_top
        analytics_repository.order_storage.get_user_order_stats_report = orig_user

    # 4. Direct DAO mock verification
    dao_order = MySQLOrderDAO()
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    row_top = MagicMock()
    row_top.user_id = 101
    row_top.user_name = "Alice"
    row_top.user_email = "alice@example.com"
    row_top.user_role = "customer"
    row_top.revenue = 500.0
    row_top.order_count = 3
    mock_res_top = MagicMock()
    mock_res_top.fetchall.return_value = [row_top]
    mock_session.execute.return_value = mock_res_top

    with patch("app.db.mysql_order_dao.get_async_session_factory", return_value=mock_factory):
        res_dao_top = await dao_order.get_top_users_by_revenue_stats(limit=5)
        assert len(res_dao_top) == 1
        assert res_dao_top[0].userId == 101
        assert type(res_dao_top[0].userId) is int
        query_top = str(mock_session.execute.call_args[0][0])
        assert "CAST(o.user_id AS CHAR)" not in query_top
        assert "o.user_id AS user_id" in query_top


@pytest.mark.asyncio
async def test_pydantic_email_and_invoice_models():
    from unittest.mock import patch
    from app.models.schemas import PopulatedOrderResponse, PopulatedOrderItemResponse, UserSnippet, Address, ReturnRequestResponse, ReturnRequestStatus
    from app.models.product import Product
    from app.utils.invoice_generator import generate_invoice_pdf
    from app.services.email_service import email_service

    prod = Product(
        id=10,
        product_id=10,
        name="Test Notebook",
        sku="NB-10",
        hsn_code="4820",
    )
    item = PopulatedOrderItemResponse(
        product=prod,
        quantity=2,
        price=150.0,
        tax_rate=18.0,
        tax_amount=27.0,
    )
    user = UserSnippet(
        name="Test Customer",
        email="customer@example.com",
        company_name="Acme Corp",
    )
    addr = Address(
        name="Test Customer",
        street="123 Main St",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
    )
    order = PopulatedOrderResponse(
        id="1001",
        order_id="ORD-1001",
        user=user,
        items=[item],
        shipping_address=addr,
        payment_method="UPI",
        total=300.0,
        shipping_charge=40.0,
        discount=20.0,
    )

    # 1. Test Invoice PDF generation with Pydantic model
    buf = await generate_invoice_pdf(order)
    pdf_bytes = buf.getvalue()
    assert pdf_bytes.startswith(b"%PDF")

    # 2. Test send_order_placed_email with Pydantic model
    from app.services.email_service import EmailService
    svc = EmailService()
    with patch.object(svc, "send_email", return_value=True) as mock_send:
        ok = svc.send_order_placed_email("customer@example.com", order)
        assert ok is True
        assert mock_send.called
        call_args = mock_send.call_args[0]
        assert "ORD-1001" in call_args[1]  # subject contains order number
        assert "Test Notebook" in call_args[3]  # html body contains item name

    # 3. Test send_order_returned_email with ReturnRequestResponse
    ret_req = ReturnRequestResponse(
        id=55,
        order_id=1001,
        user_id=12,
        items=[],
        payment_method="UPI",
        status=ReturnRequestStatus.PENDING,
        deliveryCharge=0.0,
    )
    with patch.object(svc, "send_email", return_value=True) as mock_send_ret:
        ok = svc.send_order_returned_email("customer@example.com", ret_req)
        assert ok is True
        assert mock_send_ret.called
        call_args_ret = mock_send_ret.call_args[0]
        assert "Return #55" in call_args_ret[1]
        assert "1001" in call_args_ret[2]


@pytest.mark.asyncio
async def test_batch_a_analytics_pushdowns():
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.repositories.analytics_repository import analytics_repository
    from app.models.analytics_schemas import (
        VisitorsNowResponse,
        SessionsByLandingPageResponse,
        CheckoutFunnelResponse,
        SessionsByLocationResponse,
        FunnelStage,
        FunnelStageNoDrop,
    )
    from app.db.mysql_tracking_dao import MySQLTrackingDAO
    from app.db.mysql_session_dao import MySQLSessionDAO

    # 1. Verify Repository delegation for all 4 methods
    orig_act = analytics_repository.tracking_storage.get_active_visitors_now_stats
    orig_lan = analytics_repository.tracking_storage.get_sessions_by_landing_page_stats
    orig_fun = analytics_repository.tracking_storage.get_checkout_funnel_stats
    orig_loc = analytics_repository.session_storage.get_sessions_by_location_stats

    try:
        analytics_repository.tracking_storage.get_active_visitors_now_stats = AsyncMock(
            return_value=VisitorsNowResponse(activeVisitors=15, loggedInSessions=10, guestSessions=5, windowMinutes=15)
        )
        analytics_repository.tracking_storage.get_sessions_by_landing_page_stats = AsyncMock(
            return_value=[SessionsByLandingPageResponse(landing_page="/home", sessions=50)]
        )
        analytics_repository.tracking_storage.get_checkout_funnel_stats = AsyncMock(
            return_value=CheckoutFunnelResponse(
                cart=FunnelStageNoDrop(count=100, percentage=100.0),
                shipping=FunnelStage(count=80, percentage=80.0, drop_percentage=20.0),
                review=FunnelStage(count=60, percentage=60.0, drop_percentage=25.0),
                payment=FunnelStage(count=40, percentage=40.0, drop_percentage=33.33),
                completed=FunnelStage(count=30, percentage=30.0, drop_percentage=25.0),
                overall_checkout_conversion=30.0,
            )
        )
        analytics_repository.session_storage.get_sessions_by_location_stats = AsyncMock(
            return_value=[SessionsByLocationResponse(location="Mumbai", sessions=45)]
        )

        res_act = await analytics_repository.get_active_visitors_now()
        assert res_act.activeVisitors == 15
        assert res_act.loggedInSessions == 10
        assert res_act.guestSessions == 5
        assert isinstance(res_act, VisitorsNowResponse)

        res_lan = await analytics_repository.get_sessions_by_landing_page()
        assert len(res_lan) == 1
        assert res_lan[0].landing_page == "/home"
        assert res_lan[0].sessions == 50
        assert isinstance(res_lan[0], SessionsByLandingPageResponse)

        res_fun = await analytics_repository.get_checkout_funnel()
        assert res_fun.cart.count == 100
        assert res_fun.overall_checkout_conversion == 30.0
        assert isinstance(res_fun, CheckoutFunnelResponse)

        res_loc = await analytics_repository.get_sessions_by_location()
        assert len(res_loc) == 1
        assert res_loc[0].location == "Mumbai"
        assert res_loc[0].sessions == 45
        assert isinstance(res_loc[0], SessionsByLocationResponse)
    finally:
        analytics_repository.tracking_storage.get_active_visitors_now_stats = orig_act
        analytics_repository.tracking_storage.get_sessions_by_landing_page_stats = orig_lan
        analytics_repository.tracking_storage.get_checkout_funnel_stats = orig_fun
        analytics_repository.session_storage.get_sessions_by_location_stats = orig_loc

    # 2. Verify MySQLTrackingDAO.get_active_visitors_now_stats
    tracking_dao = MySQLTrackingDAO()
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    row_act = MagicMock()
    row_act.active_visitors = 22
    row_act.logged_in_sessions = 12
    row_act.guest_sessions = 10
    mock_res_act = MagicMock()
    mock_res_act.fetchone.return_value = row_act
    mock_session.execute.return_value = mock_res_act

    with patch("app.db.mysql_tracking_dao.get_async_session_factory", return_value=mock_factory):
        dao_act = await tracking_dao.get_active_visitors_now_stats(window_minutes=15)
        assert dao_act.activeVisitors == 22
        assert dao_act.loggedInSessions == 12
        assert dao_act.guestSessions == 10
        query_act = str(mock_session.execute.call_args[0][0])
        assert "COUNT(DISTINCT session_id) AS active_visitors" in query_act
        assert "COUNT(DISTINCT CASE WHEN user_id IS NOT NULL" in query_act

    # 3. Verify MySQLTrackingDAO.get_sessions_by_landing_page_stats
    row_lan = MagicMock()
    row_lan.landing_page = "/products"
    row_lan.sessions = 75
    mock_res_lan = MagicMock()
    mock_res_lan.fetchall.return_value = [row_lan]
    mock_session.execute.return_value = mock_res_lan

    with patch("app.db.mysql_tracking_dao.get_async_session_factory", return_value=mock_factory):
        dao_lan = await tracking_dao.get_sessions_by_landing_page_stats()
        assert len(dao_lan) == 1
        assert dao_lan[0].landing_page == "/products"
        assert dao_lan[0].sessions == 75
        query_lan = str(mock_session.execute.call_args[0][0])
        assert "WITH first_pages AS" in query_lan
        assert "ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY event_timestamp ASC)" in query_lan

    # 4. Verify MySQLTrackingDAO.get_checkout_funnel_stats
    row_fun = MagicMock()
    row_fun.cart_sessions = 100
    row_fun.step1_sessions = 80
    row_fun.step2_sessions = 60
    row_fun.step3_sessions = 40
    row_fun.completed_sessions = 30
    mock_res_fun = MagicMock()
    mock_res_fun.fetchone.return_value = row_fun
    mock_session.execute.return_value = mock_res_fun

    with patch("app.db.mysql_tracking_dao.get_async_session_factory", return_value=mock_factory):
        dao_fun = await tracking_dao.get_checkout_funnel_stats()
        assert dao_fun.cart.count == 100
        assert dao_fun.shipping.count == 80
        assert dao_fun.overall_checkout_conversion == 30.0
        query_fun = str(mock_session.execute.call_args[0][0])
        assert "WITH tracking_counts AS" in query_fun
        assert "order_counts AS" in query_fun
        assert "CROSS JOIN order_counts" in query_fun

    # 5. Verify MySQLSessionDAO.get_sessions_by_location_stats
    session_dao = MySQLSessionDAO()
    row_loc = MagicMock()
    row_loc.location = "Bengaluru"
    row_loc.sessions = 120
    mock_res_loc = MagicMock()
    mock_res_loc.fetchall.return_value = [row_loc]
    mock_session.execute.return_value = mock_res_loc

    with patch("app.db.mysql_session_dao.get_async_session_factory", return_value=mock_factory):
        dao_loc = await session_dao.get_sessions_by_location_stats()
        assert len(dao_loc) == 1
        assert dao_loc[0].location == "Bengaluru"
        assert dao_loc[0].sessions == 120
        query_loc = str(mock_session.execute.call_args[0][0])
        assert "sj_analytics_sessions" in query_loc
        assert "sj_user_addresses" in query_loc
        assert "GROUP BY location" in query_loc


@pytest.mark.asyncio
async def test_final_batch_analytics_pushdowns():
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.repositories.analytics_repository import analytics_repository
    from app.models.analytics_schemas import (
        ConversionRateResponse,
        AllUserEngagementResponse,
        DurationBucket,
        UserMetric,
        UserEngagementResponse,
        ItemsByUserTypeResponse,
        FunnelStage,
        FunnelStageNoDrop,
    )
    from app.db.mysql_tracking_dao import MySQLTrackingDAO
    from app.db.mysql_session_dao import MySQLSessionDAO

    # 1. Verify Repository delegation for all 4 methods
    orig_conv = analytics_repository.tracking_storage.get_conversion_funnel_stats
    orig_all_eng = analytics_repository.session_storage.get_all_user_engagement_aggregate_stats
    orig_user_eng = analytics_repository.session_storage.get_user_engagement_metrics_stats
    orig_items_type = analytics_repository.tracking_storage.get_items_by_user_type_stats

    try:
        analytics_repository.tracking_storage.get_conversion_funnel_stats = AsyncMock(
            return_value=ConversionRateResponse(
                sessions=FunnelStageNoDrop(count=100, percentage=100.0),
                added_to_cart=FunnelStage(count=50, percentage=50.0, drop_percentage=50.0),
                reached_checkout=FunnelStage(count=30, percentage=30.0, drop_percentage=40.0),
                completed=FunnelStage(count=10, percentage=10.0, drop_percentage=66.67),
                overall_conversion_rate=10.0,
            )
        )
        analytics_repository.session_storage.get_all_user_engagement_aggregate_stats = AsyncMock(
            return_value=AllUserEngagementResponse(
                duration_buckets=[DurationBucket(range="0-60s", count=5)],
                user_metrics=[
                    UserMetric(
                        userId=101,
                        name="Alice",
                        email="alice@example.com",
                        averageSessionTimeSeconds=45.0,
                        totalSessions=2,
                    )
                ],
            )
        )
        analytics_repository.session_storage.get_user_engagement_metrics_stats = AsyncMock(
            return_value=UserEngagementResponse(
                userId=101,
                registrationDate="2026-01-01T00:00:00",
                totalSessions=5,
                averageSessionTimeSeconds=120.0,
                averageDaysBetweenSessions=2.5,
                averagePagesPerSession=4.0,
                sessionsWithOrder=2,
                sessionOrderRate=0.4,
            )
        )
        analytics_repository.tracking_storage.get_items_by_user_type_stats = AsyncMock(
            return_value=[
                ItemsByUserTypeResponse(role="customer", views=100, searches=50),
                ItemsByUserTypeResponse(role="guest", views=20, searches=10),
            ]
        )

        res_conv = await analytics_repository.get_conversion_rate_over_time()
        assert res_conv.sessions.count == 100
        assert res_conv.overall_conversion_rate == 10.0
        assert isinstance(res_conv, ConversionRateResponse)

        res_all_eng = await analytics_repository.get_all_user_engagement_aggregate()
        assert len(res_all_eng.duration_buckets) == 1
        assert len(res_all_eng.user_metrics) == 1
        assert res_all_eng.user_metrics[0].userId == 101
        assert isinstance(res_all_eng.user_metrics[0].userId, int)
        assert isinstance(res_all_eng, AllUserEngagementResponse)

        res_user_eng = await analytics_repository.get_user_engagement_metrics(101)
        assert res_user_eng.userId == 101
        assert isinstance(res_user_eng.userId, int)
        assert res_user_eng.totalSessions == 5
        assert res_user_eng.sessionOrderRate == 0.4
        assert isinstance(res_user_eng, UserEngagementResponse)

        res_items_type = await analytics_repository.get_items_by_user_type()
        assert len(res_items_type) == 2
        assert res_items_type[0].role == "customer"
        assert isinstance(res_items_type[0], ItemsByUserTypeResponse)
    finally:
        analytics_repository.tracking_storage.get_conversion_funnel_stats = orig_conv
        analytics_repository.session_storage.get_all_user_engagement_aggregate_stats = orig_all_eng
        analytics_repository.session_storage.get_user_engagement_metrics_stats = orig_user_eng
        analytics_repository.tracking_storage.get_items_by_user_type_stats = orig_items_type

    # 2. Direct DAO: MySQLTrackingDAO.get_conversion_funnel_stats
    tracking_dao = MySQLTrackingDAO()
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session

    row_conv = MagicMock()
    row_conv.session_count = 100
    row_conv.added_to_cart_count = 50
    row_conv.reached_checkout_count = 30
    row_conv.completed_sessions = 10
    mock_res_conv = MagicMock()
    mock_res_conv.fetchone.return_value = row_conv
    mock_session.execute.return_value = mock_res_conv

    with patch("app.db.mysql_tracking_dao.get_async_session_factory", return_value=mock_factory):
        dao_conv = await tracking_dao.get_conversion_funnel_stats()
        assert dao_conv.sessions.count == 100
        assert dao_conv.added_to_cart.count == 50
        assert dao_conv.overall_conversion_rate == 10.0
        query_conv = str(mock_session.execute.call_args[0][0])
        assert "WITH tracking_counts AS" in query_conv
        assert "order_counts AS" in query_conv
        assert "event_type = 'cart_add'" in query_conv

    # 3. Direct DAO: MySQLTrackingDAO.get_items_by_user_type_stats
    row_items = MagicMock()
    row_items.role = "customer"
    row_items.views = 42
    row_items.searches = 15
    mock_res_items = MagicMock()
    mock_res_items.fetchall.return_value = [row_items]
    mock_session.execute.return_value = mock_res_items

    with patch("app.db.mysql_tracking_dao.get_async_session_factory", return_value=mock_factory):
        dao_items = await tracking_dao.get_items_by_user_type_stats()
        assert len(dao_items) == 1
        assert dao_items[0].role == "customer"
        assert dao_items[0].views == 42
        query_items = str(mock_session.execute.call_args[0][0])
        assert "WHEN t.user_id IS NULL" in query_items
        assert "GROUP BY role" in query_items

    # 4. Direct DAO: MySQLSessionDAO.get_all_user_engagement_aggregate_stats
    session_dao = MySQLSessionDAO()
    row_agg = MagicMock()
    row_agg.user_id = 101
    row_agg.name = "Bob"
    row_agg.email = "bob@example.com"
    row_agg.average_session_time_seconds = 150.0
    row_agg.total_sessions = 3
    mock_res_agg = MagicMock()
    mock_res_agg.fetchall.return_value = [row_agg]
    mock_session.execute.return_value = mock_res_agg

    with patch("app.db.mysql_session_dao.get_async_session_factory", return_value=mock_factory):
        dao_agg = await session_dao.get_all_user_engagement_aggregate_stats()
        assert len(dao_agg.user_metrics) == 1
        assert dao_agg.user_metrics[0].userId == 101
        assert isinstance(dao_agg.user_metrics[0].userId, int)
        assert dao_agg.user_metrics[0].averageSessionTimeSeconds == 150.0
        assert any(b.range == "60-300s" and b.count == 1 for b in dao_agg.duration_buckets)
        query_agg = str(mock_session.execute.call_args[0][0])
        assert "WITH user_session_agg AS" in query_agg
        assert "TIMESTAMPDIFF(SECOND" in query_agg

    # 5. Direct DAO: MySQLSessionDAO.get_user_engagement_metrics_stats
    row_user = MagicMock()
    row_user.user_id = 101
    row_user.registration_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    row_user.total_sessions = 5
    row_user.average_session_time_seconds = 180.0
    row_user.average_days_between_sessions = 3.2
    row_user.average_pages_per_session = 4.5
    row_user.sessions_with_order = 2
    row_user.session_order_rate = 0.4

    mock_res_user = MagicMock()
    mock_res_user.fetchone.return_value = row_user
    mock_session.execute.return_value = mock_res_user

    with patch("app.db.mysql_session_dao.get_async_session_factory", return_value=mock_factory):
        dao_user = await session_dao.get_user_engagement_metrics_stats(101)
        assert dao_user.userId == 101
        assert isinstance(dao_user.userId, int)
        assert dao_user.totalSessions == 5
        assert dao_user.averageSessionTimeSeconds == 180.0
        assert dao_user.averageDaysBetweenSessions == 3.2
        assert dao_user.averagePagesPerSession == 4.5
        assert dao_user.sessionsWithOrder == 2
        assert dao_user.sessionOrderRate == 0.4
        query_user = str(mock_session.execute.call_args[0][0])
        assert "WITH user_info AS" in query_user
        assert "valid_sessions AS" in query_user
        assert "session_metrics AS" in query_user
        assert "pages_per_session AS" in query_user
        assert "order_metrics AS" in query_user
        assert "CROSS JOIN order_metrics" in query_user










