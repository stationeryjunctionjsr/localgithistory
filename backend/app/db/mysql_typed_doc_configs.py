"""
Configs for MySQLTypedDocDAO: parent-only tables with fixed columns + JSON columns.
No child tables. Keys are API (camelCase); values are DB column names (snake_case).
"""

from typing import Dict, Optional, Set

from app.db.mysql_typed_doc_dao import MySQLTypedDocDAO


def _dao(
    table: str,
    scalar: Dict[str, str],
    clob: Optional[Dict[str, str]] = None,
    bool_keys: Optional[Set[str]] = None,
) -> MySQLTypedDocDAO:
    return MySQLTypedDocDAO(
        table_name=table,
        scalar_map=scalar,
        clob_map=clob or {},
        bool_api_keys=bool_keys or frozenset(),
    )


# Collection name -> MySQLTypedDocDAO instance (parent-only; no child tables)
TYPED_DOC_DAOS = {
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
    "google_reviews": _dao(
        "sj_google_reviews",
        {"rating": "rating", "reviewCount": "review_count", "lastUpdated": "last_updated", "method": "method"},
    ),
    "stockReservations": _dao(
        "sj_stock_reservations",
        {
            "productId": "product_id",
            "userId": "user_id",
            "quantity": "quantity",
            "status": "status",
            "expiresAt": "expires_at",
        },
    ),
    "productNotifications": _dao(
        "sj_product_notifications",
        {"productId": "product_id", "userId": "user_id", "email": "email", "phone": "phone", "status": "status"},
    ),
    "productReviews": _dao(
        "sj_product_reviews",
        {
            "productId": "product_id",
            "userId": "user_id",
            "rating": "rating",
            "reviewText": "review_text",
            "status": "status",
        },
    ),
    "reviewClassifications": _dao(
        "sj_review_classifications",
        {
            "reviewId": "review_id",
            "category": "category",
            "confidenceScore": "confidence_score",
            "sentiment": "sentiment",
        },
    ),
    "aboutUs": _dao(
        "sj_about_us",
        {"title": "title", "content": "content", "version": "version", "isPublished": "is_published"},
        None,
        frozenset({"isPublished"}),
    ),
    "privacyPolicy": _dao(
        "sj_privacy_policy",
        {"version": "version", "content": "content", "effectiveDate": "effective_date", "isActive": "is_active"},
        None,
        frozenset({"isActive"}),
    ),
    "availabilityRequests": _dao(
        "sj_availability_requests",
        {
            "productId": "product_id",
            "productName": "product_name",
            "pincode": "pincode",
            "userName": "user_name",
            "userEmail": "user_email",
        },
    ),
    "pincodeSearches": _dao(
        "sj_pincode_searches",
        {"pincode": "pincode", "query": "query", "isServiceable": "is_serviceable", "timestamp": "timestamp"},
        None,
        frozenset({"isServiceable"}),
    ),
    "systemSettings": _dao(
        "sj_system_settings",
        {
            "maintenanceMode": "maintenance_mode",
            "allowSignups": "allow_signups",
            "maxUploadSizeMb": "max_upload_size_mb",
            "defaultCurrency": "default_currency",
            "timezone": "timezone",
        },
        None,
        frozenset({"maintenanceMode", "allowSignups"}),
    ),
    "valetPayoutSettings": _dao(
        "sj_valet_payout_settings",
        {
            "deliveryChargePerOrder": "delivery_charge_per_order",
            "returnPickupChargePerOrder": "return_pickup_charge_per_order",
        },
    ),
}
