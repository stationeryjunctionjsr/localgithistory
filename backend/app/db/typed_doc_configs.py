"""
Configs for TypedDocDAO: parent-only tables with fixed columns + JSON columns.
No child tables. Keys are API (camelCase); values are DB column names (snake_case).
"""

from app.config.settings import settings
from typing import Dict, Optional, Set

from app.db.typed_doc_dao import TypedDocDAO


def _dao(
    table: str,
    scalar: Dict[str, str],
    clob: Optional[Dict[str, str]] = None,
    bool_keys: Optional[Set[str]] = None,
) -> TypedDocDAO:
    return TypedDocDAO(
        table_name=table,
        scalar_map=scalar,
        clob_map=clob or {},
        bool_api_keys=bool_keys or frozenset(),
    )


# Collection name -> TypedDocDAO instance (parent-only; no child tables)
TYPED_DOC_DAOS = {
    "activities": _dao(
        "sj_activities",
        {
            "userId": "user_id",
            "sessionId": "session_id",
            "action": "action",
            "comment": "comments",
            "isGuest": "is_guest",
            "userAgent": "user_agent",
            "os": "os",
            "osVersion": "os_version",
            "deviceType": "device_type",
            "appVersion": "app_version",
            "deviceModel": "device_model",
            "locale": "locale",
            "ip": "ip",
        },
        {"meta": "meta"},
        frozenset({"isGuest"}),
    ),
    "notifications": _dao(
        "sj_notifications",
        {
            "userId": "user_id",
            "type": "type",
            "title": "title",
            "message": "message",
            "isRead": "is_read",
            "isAcknowledged": "is_acknowledged",
        },
        {"data": "data"},
        frozenset({"isRead", "isAcknowledged"}),
    ),
    "returnRequests": _dao(
        "sj_return_requests",
        {
            "returnId": "return_id",
            "orderId": "order_id",
            "userId": "user_id",
            "sellerId": "seller_id",
            "deliverySlotId": "delivery_slot_id",
            "deliverySlotConfigId": "delivery_slot_config_id",
            "deliverySlotDate": "delivery_slot_date",
            "paymentMethod": "payment_method",
            "upiPaymentScreenshot": "upi_payment_screenshot",
            "notes": "notes",
            "status": "status",
            "valetId": "valet_id",
            "pendingValetId": "pending_valet_id",
            "valetAssignedAt": "valet_assigned_at",
            "valetCascadeCount": "valet_cascade_count",
            "valetAcceptedAt": "valet_accepted_at",
            "valetDeclinedAt": "valet_declined_at",
            "valetDeclineReason": "valet_decline_reason",
            "deliveryCharge": "delivery_charge",
        },
        {"items": "items", "valetDeclineHistory": "valet_decline_history"},
    ),
    "returnSettings": _dao(
        "sj_return_settings",
        {"returnDays": "return_days"},
    ),
    "schemes": _dao(
        "sj_schemes",
        {
            "name": "name",
            "description": "description",
            "discountType": "discount_type",
            "discountValue": "discount_value",
            "minOrderValue": "min_order_value",
            "validFrom": "valid_from",
            "validUntil": "valid_until",
            "isActive": "is_active",
            "code": "code",
        },
        {"applicableRoles": "applicable_roles"},
        frozenset({"isActive"}),
    ),
    "contacts": _dao(
        "sj_contacts",
        {
            "email": "email",
            "description": "description",
            "isActive": "is_active",
            "displayOrder": "display_order",
        },
        {"addresses": "addresses", "phoneNumbers": "phone_numbers"},
        frozenset({"isActive"}),
    ),
    "supportTickets": _dao(
        "sj_support_tickets",
        {
            "ticketNumber": "ticket_number",
            "user": "user_id",
            "name": "name",
            "email": "email",
            "phone": "phone",
            "company": "company",
            "subject": "subject",
            "description": "description",
            "category": "category",
            "priority": "priority",
            "status": "status",
            "assignedTo": "assigned_to",
            "resolvedAt": "resolved_at",
            "closedAt": "closed_at",
        },
        {"attachments": "attachments", "responses": "responses"},
    ),
    "orderFeedback": _dao(
        "sj_order_feedback",
        {
            "orderId": "order_id",
            "userId": "user_id",
            "rating": "rating",
            "comment": "comments",
            "deliveryRating": "delivery_rating",
            "deliveryComment": "delivery_comment",
            "feedbackType": "feedback_type",
        },
    ),
    "promoStrips": _dao(
        "sj_promo_strips",
        {"text": "text", "isActive": "is_active"},
        bool_keys=frozenset({"isActive"}),
    ),
    "pushNotifications": _dao(
        "sj_push_notifications",
        {
            "title": "title",
            "message": "message",
            "link": "link",
            "image": "image",
            "status": "status",
            "scheduledFor": "scheduled_for",
            "deliveredCount": "delivered_count",
            "readCount": "read_count",
            "userSegment": "user_segment",
            "userBehavior": "user_behavior",
            "createdBy": "created_by",
        },
    ),
    "deviceSubscriptions": _dao(
        "sj_device_subscriptions",
        {"userId": "user_id", "endpoint": "endpoint", "expoToken": "expo_token"},
        {"keys": "keys", "subscription": "subscription"},
    ),
    "collections": _dao(
        "sj_collections",
        {
            "name": "name",
            "description": "description",
            "imageUrl": "image_url",
            "isActive": "is_active",
            "displayOrder": "display_order",
        },
        {
            "visiblePages": "visible_pages",
            "userSegments": "user_segments",
            "visibilityRules": "visibility_rules",
            "productIds": "product_ids",
        },
        frozenset({"isActive"}),
    ),
    "searchTags": _dao(
        "sj_search_tags",
        {
            "tagId": "tag_id",
            "name": "name",
            "type": "type",
            "isActive": "is_active",
        },
        {
            "categories": "categories",
            "subCategories": "sub_categories",
            "brands": "brands",
            "collections": "collections",
            "productIds": "product_ids",
            "excludedProductIds": "excluded_product_ids",
        },
        frozenset({"isActive"}),
    ),
    "coachMarks": _dao(
        "sj_coach_marks",
        {
            "anchorId": "anchor_id",
            "title": "title",
            "description": "description",
            "screenName": "screen_name",
            "sequenceOrder": "sequence_order",
            "isActive": "is_active",
        },
        bool_keys=frozenset({"isActive"}),
    ),
    "categoryTags": _dao(
        "sj_category_tags",
        {"name": "name", "description": "description", "isActive": "is_active"},
        bool_keys=frozenset({"isActive"}),
    ),
    "deliveryCharges": _dao(
        "sj_delivery_charges",
        {
            "locationId": "location_id",
            "pincode": "pincode",
            "state": "state",
            "city": "city",
            "district": "district",
            "applyDefaultCharge": "apply_default_charge",
            "charge": "charge",
            "minCartValue": "min_cart_value",
            "serviceableForCustomer": "serviceable_for_customer",
            "serviceableForRetailer": "serviceable_for_retailer",
            "serviceableForWholesaler": "serviceable_for_wholesaler",
            "isActive": "is_active",
            "description": "description",
        },
        {"tiers": "tiers"},
        frozenset(
            {
                "applyDefaultCharge",
                "serviceableForCustomer",
                "serviceableForRetailer",
                "serviceableForWholesaler",
                "isActive",
            }
        ),
    ),
    "deliveryChargeDefaults": _dao(
        "sj_delivery_charge_defaults",
        {
            "applicableToWholesaler": "applicable_to_wholesaler",
            "applicableToRetailer": "applicable_to_retailer",
            "isActive": "is_active",
        },
        {"tiers": "tiers"},
        frozenset({"applicableToWholesaler", "applicableToRetailer", "isActive"}),
    ),
    "deliverySlots": _dao(
        "sj_delivery_slots",
        {
            "segment": "segment",
            "date": "date",
            "isActive": "is_active",
        },
        {"slots": "slots", "pincodes": "pincodes"},
        frozenset({"isActive"}),
    ),
    "events": _dao(
        "sj_events",
        {"eventType": "event_type"},
        {"payload": "payload"},
    ),
    "customerSegments": _dao(
        "sj_customer_segments",
        {"type": "type"},
        {"payload": "payload"},
    ),
    "google_reviews": _dao(
        "sj_google_reviews",
        {"rating": "rating", "reviewCount": "review_count", "lastUpdated": "last_updated", "method": "method"},
    ),
}
