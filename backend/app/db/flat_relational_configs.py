from app.models.daos import NotificationInternal
from app.models.schemas import SupportTicketInternal
from app.models.daos_flat import CouponInternal, DeliverySlotConfigInternal, DeliveryZoneInternal, DeliveryChargeDefaultInternal, DeliveryChargeInternal, CategoryTagInternal, CoachMarkInternal, SearchTagInternal, CollectionInternal, DeviceSubscriptionInternal, PushNotificationsInternal, PromoStripsInternal, OrderFeedbackInternal, ContactInternal, SchemeInternal, ReturnSettingsInternal, ActivityInternal, ReturnRequestInternal
from app.models.schemas import SearchTagResponse, CollectionResponse, SchemeResponse, DeliveryChargeResponse, DefaultDeliveryChargeResponse
"""
Configs for FlatRelationalDAO: parent-only tables with fixed columns + JSON columns.
No child tables. Keys are API (camelCase); values are DB column names (snake_case).
"""

from app.config.settings import settings
from typing import Dict, Optional, Set

from app.db.flat_relational_dao import FlatRelationalDAO


def _dao(
    table: str,
    scalar: Dict[str, str],
    bool_keys: Optional[Set[str]] = None,
    schema_cls=None,
    clob: Optional[Dict[str, str]] = None,
) -> FlatRelationalDAO:
    return FlatRelationalDAO(
        table_name=table,
        scalar_map=scalar,
        clob_map=clob or {},
        bool_api_keys=bool_keys or frozenset(),
        schema_cls=schema_cls,
    )


# Collection name -> FlatRelationalDAO instance (parent-only; no child tables)
FLAT_RELATIONAL_DAOS = {
    "coupons": _dao(
        "sj_coupons",
        {
            "code": "code",
            "discountType": "discount_type",
            "discountValue": "discount_value",
            "minOrderValue": "min_order_value",
            "maxUses": "max_uses",
            "usedCount": "used_count",
            "validFrom": "start_date",
            "validUntil": "end_date",
            "isActive": "is_active",
            "typeOfDiscount": "type_of_discount",
            "method": "method",
            "minRequirementType": "min_requirement_type",
            "minQuantityOfEligibleItems": "min_quantity_of_eligible_items",
            "maxDiscountAmount": "max_discount_amount",
            "appliesToType": "applies_to_type"
        },
        {},
        schema_cls=CouponInternal
    ),

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
        bool_keys=frozenset({"isGuest"}),
        schema_cls=ActivityInternal
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
        bool_keys=frozenset({"isRead", "isAcknowledged"}),
        schema_cls=NotificationInternal
    ),
    "returnRequests": _dao(
        "sj_return_requests",
        {
            "returnId": "return_id",
            "orderId": "order_id",
            "userId": "user_id",
            "paymentMethod": "payment_method",
            "upiPaymentScreenshot": "upi_payment_screenshot",
            "notes": "notes",
            "status": "status",
            "valetId": "valet_id",
            "sellerId": "seller_id",
            "deliverySlotId": "delivery_slot_id",
            "deliverySlotConfigId": "delivery_slot_config_id",
            "deliverySlotDate": "delivery_slot_date",
            "pendingValetId": "pending_valet_id",
            "valetAssignedAt": "valet_assigned_at",
            "valetCascadeCount": "valet_cascade_count",
            "deliveryCharge": "delivery_charge",
        },
        schema_cls=ReturnRequestInternal
    ),
    "returnSettings": _dao(
        "sj_return_settings",
        {"returnDays": "return_days"},
        schema_cls=ReturnSettingsInternal
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
        bool_keys=frozenset({"isActive"}),
        schema_cls=SchemeInternal
    ),
    "contacts": _dao(
        "sj_contacts",
        {
            "email": "email",
            "description": "description",
            "isActive": "is_active",
            "displayOrder": "display_order",
        },
        bool_keys=frozenset({"isActive"}),
        schema_cls=ContactInternal
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
        schema_cls=SupportTicketInternal
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
        schema_cls=OrderFeedbackInternal
    ),
    "promoStrips": _dao(
        "sj_promo_strips",
        {"text": "text", "isActive": "is_active"},
        bool_keys=frozenset({"isActive"}),
        schema_cls=PromoStripsInternal
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
        schema_cls=PushNotificationsInternal
    ),
    "deviceSubscriptions": _dao(
        "sj_device_subscriptions",
        {"userId": "user_id", "endpoint": "endpoint", "expoToken": "expo_token"},
        schema_cls=DeviceSubscriptionInternal
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
        bool_keys=frozenset({"isActive"}),
        schema_cls=CollectionInternal
    ),
    "searchTags": _dao(
        "sj_search_tags",
        {
            "tagId": "tag_id",
            "name": "name",
            "type": "type",
            "isActive": "is_active",
        },
        bool_keys=frozenset({"isActive"}),
        schema_cls=SearchTagInternal
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
        schema_cls=CoachMarkInternal
    ),
    "categoryTags": _dao(
        "sj_category_tags",
        {"name": "name", "description": "description", "isActive": "is_active"},
        bool_keys=frozenset({"isActive"}),
        schema_cls=CategoryTagInternal
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
            "urgentDeliveryAvailable": "urgent_delivery_available",
            "urgentDeliveryCharge": "urgent_delivery_charge",
        },
        bool_keys=frozenset(
            {
                "applyDefaultCharge",
                "serviceableForCustomer",
                "serviceableForRetailer",
                "serviceableForWholesaler",
                "isActive",
                "urgentDeliveryAvailable",
            }
        ),
        schema_cls=DeliveryChargeInternal
    ),
    "deliveryChargeDefaults": _dao(
        "sj_delivery_charge_defaults",
        {
            "applicableToWholesaler": "applicable_to_wholesaler",
            "applicableToRetailer": "applicable_to_retailer",
            "isActive": "is_active",
        },
        bool_keys=frozenset({"applicableToWholesaler", "applicableToRetailer", "isActive"}),
        schema_cls=DeliveryChargeDefaultInternal
    ),
    "deliveryZones": _dao(
        "sj_delivery_zones",
        {
            "name": "name",
            "description": "description",
            "defaultCapacity": "default_capacity",
            "urgentDeliveryAvailable": "urgent_delivery_available",
            "customerType": "customer_type",
            "isActive": "is_active",
        },
        bool_keys=frozenset({"urgentDeliveryAvailable", "isActive"}),
        schema_cls=DeliveryZoneInternal
    ),
    "deliverySlots": _dao(
        "sj_delivery_slots",
        {
            "segment": "segment",
            "date": "date",
            "zoneId": "zone_id",
            "isActive": "is_active",
        },
        bool_keys=frozenset({"isActive"}),
        schema_cls=DeliverySlotConfigInternal
    ),
    "events": _dao(
        "sj_events",
        {"eventType": "event_type"},
    ),
    "customerSegments": _dao(
        "sj_customer_segments",
        {"type": "type"},
    ),
    "google_reviews": _dao(
        "sj_google_reviews",
        {"rating": "rating", "reviewCount": "review_count", "lastUpdated": "last_updated", "method": "method"},
    ),
}




