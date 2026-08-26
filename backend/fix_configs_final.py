with open("backend/app/db/mysql_typed_doc_configs.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# delete everything after deliveryCharges (around line 226-253)
# let's find the line index for "deliveryCharges"
del_idx = -1
for i, l in enumerate(lines):
    if '"deliveryCharges": _dao(' in l:
        del_idx = i
        break

if del_idx != -1:
    # keep lines up to deliveryCharges
    lines_to_keep = lines[:del_idx]

    # manually append the rest
    rest = """    "deliveryCharges": _dao(
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
        frozenset({
            "applyDefaultCharge",
            "serviceableForCustomer",
            "serviceableForRetailer",
            "serviceableForWholesaler",
            "isActive",
        })
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
    "deliveryZones": _dao(
        "sj_delivery_zones",
        {
            "name": "name",
            "description": "description",
            "defaultCapacity": "default_capacity",
            "urgentDeliveryAvailable": "urgent_delivery_available",
            "isActive": "is_active",
        },
        {"pincodes": "pincodes"},
        frozenset({"urgentDeliveryAvailable", "isActive"}),
    ),
    "events": _dao(
        "sj_events",
        {"eventType": "event_type"},
        {"payload": "payload"},
    ),
    "google_reviews": _dao(
        "sj_google_reviews",
        {"rating": "rating", "reviewCount": "review_count", "lastUpdated": "last_updated", "method": "method"},
    ),
    "stockReservations": _dao(
        "sj_stock_reservations",
        {"productId": "product_id", "userId": "user_id", "quantity": "quantity", "status": "status", "expiresAt": "expires_at"}
    ),
    "productNotifications": _dao(
        "sj_product_notifications",
        {"productId": "product_id", "userId": "user_id", "email": "email", "phone": "phone", "status": "status"}
    ),
    "productReviews": _dao(
        "sj_product_reviews",
        {"productId": "product_id", "userId": "user_id", "rating": "rating", "reviewText": "review_text", "status": "status"}
    ),
    "reviewClassifications": _dao(
        "sj_review_classifications",
        {"reviewId": "review_id", "category": "category", "confidenceScore": "confidence_score", "sentiment": "sentiment"}
    ),
    "customerSegments": _dao(
        "sj_customer_segments",
        {"type": "type", "name": "name", "description": "description", "isActive": "is_active"},
        {"criteria": "criteria"},
        frozenset({"isActive"})
    ),
    "faqSections": _dao(
        "sj_faq_sections",
        {"title": "title", "orderIndex": "order_index", "isActive": "is_active"},
        {"faqs": "faqs"},
        frozenset({"isActive"})
    ),
    "aboutUs": _dao(
        "sj_about_us",
        {"title": "title", "content": "content", "version": "version", "isPublished": "is_published"},
        None,
        frozenset({"isPublished"})
    ),
    "privacyPolicy": _dao(
        "sj_privacy_policy",
        {"version": "version", "content": "content", "effectiveDate": "effective_date", "isActive": "is_active"},
        None,
        frozenset({"isActive"})
    ),
    "availabilityRequests": _dao(
        "sj_availability_requests",
        {"productId": "product_id", "productName": "product_name", "pincode": "pincode", "userName": "user_name", "userEmail": "user_email"}
    ),
    "commissionSettings": _dao(
        "sj_commission_settings",
        {"defaultCommissionPct": "default_commission_pct"},
        {"tiers": "tiers"}
    ),
    "pincodeSearches": _dao(
        "sj_pincode_searches",
        {"pincode": "pincode", "query": "query", "isServiceable": "is_serviceable", "timestamp": "timestamp"},
        None,
        frozenset({"isServiceable"})
    ),
    "systemSettings": _dao(
        "sj_system_settings",
        {"maintenanceMode": "maintenance_mode", "allowSignups": "allow_signups", "maxUploadSizeMb": "max_upload_size_mb", "defaultCurrency": "default_currency", "timezone": "timezone"},
        None,
        frozenset({"maintenanceMode", "allowSignups"})
    ),
    "valetAvailability": _dao(
        "sj_valet_availability",
        {"date": "date", "availabilityType": "availability_type"},
        {"slots": "slots", "zones": "zones"}
    ),
    "valetPayoutSettings": _dao(
        "sj_valet_payout_settings",
        {"deliveryChargePerOrder": "delivery_charge_per_order", "returnPickupChargePerOrder": "return_pickup_charge_per_order"}
    ),
}
"""
    with open("backend/app/db/mysql_typed_doc_configs.py", "w", encoding="utf-8") as f:
        f.writelines(lines_to_keep)
        f.write(rest)
