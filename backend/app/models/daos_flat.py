from app.models.base import CamelBaseModel
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Optional, Dict, List
from datetime import datetime
from app.models.schemas import TicketResponseItemInternal, SocialMedia
from app.models.daos import CustomerSegmentFilters

class ReturnSettingsInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    return_days: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ReturnSettingsInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    return_days: Optional[int] = None

class ReturnSettingsInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    return_days: Optional[int] = None

class SchemeInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: Optional[bool] = None
    code: Optional[str] = None
    applicable_roles: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SchemeInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: Optional[bool] = None
    code: Optional[str] = None
    applicable_roles: Optional[List[str]] = None

class SchemeInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: Optional[bool] = None
    code: Optional[str] = None
    applicable_roles: Optional[List[str]] = None

class ContactInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    email: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    addresses: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    social_media: Optional[SocialMedia] = None

class ContactInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    email: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    addresses: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None
    social_media: Optional[SocialMedia] = None

class ContactInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    email: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    addresses: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None
    social_media: Optional[SocialMedia] = None

class OrderFeedbackInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    comment: Optional[str] = None
    delivery_comment: Optional[str] = None
    delivery_rating: Optional[int] = None
    feedback_type: Optional[str] = None
    order_id: Optional[str] = None
    rating: Optional[int] = None
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class OrderFeedbackInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    comment: Optional[str] = None
    delivery_comment: Optional[str] = None
    delivery_rating: Optional[int] = None
    feedback_type: Optional[str] = None
    order_id: Optional[str] = None
    rating: Optional[int] = None
    user_id: Optional[str] = None

class OrderFeedbackInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    comment: Optional[str] = None
    delivery_comment: Optional[str] = None
    delivery_rating: Optional[int] = None
    feedback_type: Optional[str] = None
    order_id: Optional[str] = None
    rating: Optional[int] = None
    user_id: Optional[str] = None

class PromoStripsInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    is_active: Optional[bool] = None
    text: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    zone_ids: Optional[List[str]] = None

class DeviceKeyInternal(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    key: str
    value: str

class DeviceSubscriptionInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    expo_token: Optional[str] = None
    keys: Optional[List[DeviceKeyInternal]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DeviceSubscriptionInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    expo_token: Optional[str] = None
    keys: Optional[List[DeviceKeyInternal]] = None

class DeviceSubscriptionInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    expo_token: Optional[str] = None
    keys: Optional[List[DeviceKeyInternal]] = None

class CollectionInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    external_id: Optional[str] = None
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    visible_pages: Optional[List[str]] = None
    user_segments: Optional[List[str]] = None
    visibility_rules: Optional[List[Any]] = None
    product_ids: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CollectionInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    external_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    visible_pages: Optional[List[str]] = None
    user_segments: Optional[List[str]] = None
    visibility_rules: Optional[List[Any]] = None
    product_ids: Optional[List[str]] = None

class CollectionInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    external_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    visible_pages: Optional[List[str]] = None
    user_segments: Optional[List[str]] = None
    visibility_rules: Optional[List[Any]] = None
    product_ids: Optional[List[str]] = None

class SearchTagInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    tag_id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    categories: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    product_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SearchTagInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    tag_id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    categories: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    product_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None

class SearchTagInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    tag_id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    categories: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    product_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None

class CoachMarkInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    anchor_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CoachMarkInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    anchor_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    is_active: Optional[bool] = None

class CoachMarkInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    anchor_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    is_active: Optional[bool] = None

class CategoryTagInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CategoryTagInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CategoryTagInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class DeliveryChargeTierInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    min: Optional[float] = None
    max: Optional[float] = None
    charge: Optional[float] = None

class DeliveryChargeInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    location_id: Optional[int] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    apply_default_charge: Optional[bool] = None
    charge: Optional[float] = None
    min_cart_value: Optional[float] = None
    serviceable_for_customer: Optional[bool] = None
    serviceable_for_wholesaler: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    urgent_delivery_available: Optional[bool] = None
    urgent_delivery_charge: Optional[float] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DeliveryChargeInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    location_id: Optional[int] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    apply_default_charge: Optional[bool] = None
    charge: Optional[float] = None
    min_cart_value: Optional[float] = None
    serviceable_for_customer: Optional[bool] = None
    serviceable_for_wholesaler: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    urgent_delivery_available: Optional[bool] = None
    urgent_delivery_charge: Optional[float] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliveryChargeInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    location_id: Optional[int] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    apply_default_charge: Optional[bool] = None
    charge: Optional[float] = None
    min_cart_value: Optional[float] = None
    serviceable_for_customer: Optional[bool] = None
    serviceable_for_wholesaler: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    urgent_delivery_available: Optional[bool] = None
    urgent_delivery_charge: Optional[float] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliveryChargeDefaultInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    applicable_to_wholesaler: Optional[bool] = None
    applicable_to_retailer: Optional[bool] = None
    charge: Optional[float] = None
    urgent_delivery_available: Optional[bool] = None
    urgent_delivery_charge: Optional[float] = None
    is_active: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DeliveryChargeDefaultInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    applicable_to_wholesaler: Optional[bool] = None
    applicable_to_retailer: Optional[bool] = None
    charge: Optional[float] = None
    urgent_delivery_available: Optional[bool] = None
    urgent_delivery_charge: Optional[float] = None
    is_active: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliveryChargeDefaultInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    applicable_to_wholesaler: Optional[bool] = None
    applicable_to_retailer: Optional[bool] = None
    charge: Optional[float] = None
    urgent_delivery_available: Optional[bool] = None
    urgent_delivery_charge: Optional[float] = None
    is_active: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliveryZoneInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    description: Optional[str] = None
    default_capacity: Optional[int] = None
    urgent_delivery_available: Optional[bool] = None
    customer_type: Optional[str] = None
    is_active: Optional[bool] = None
    pincodes: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DeliveryZoneInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    default_capacity: Optional[int] = None
    urgent_delivery_available: Optional[bool] = None
    customer_type: Optional[str] = None
    is_active: Optional[bool] = None
    pincodes: Optional[List[str]] = None

class DeliveryZoneInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    default_capacity: Optional[int] = None
    urgent_delivery_available: Optional[bool] = None
    customer_type: Optional[str] = None
    is_active: Optional[bool] = None
    pincodes: Optional[List[str]] = None

class DeliverySlotInternal(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    capacity: Optional[int] = None
    booked_count: Optional[int] = 0
    is_full_day: Optional[bool] = False
    is_urgent: Optional[bool] = False
    cutoff_hours: Optional[int] = None
    urgent_cutoff_hours: Optional[int] = None
    is_active: Optional[bool] = True

class DeliverySlotConfigInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    segment: Optional[str] = None
    date: Optional[str] = None
    zone_id: Optional[str] = None
    is_active: Optional[bool] = None
    slots: Optional[List[DeliverySlotInternal]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DeliverySlotConfigInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    segment: Optional[str] = None
    date: Optional[str] = None
    zone_id: Optional[str] = None
    is_active: Optional[bool] = None
    slots: Optional[List[DeliverySlotInternal]] = None

class DeliverySlotConfigInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    segment: Optional[str] = None
    date: Optional[str] = None
    zone_id: Optional[str] = None
    is_active: Optional[bool] = None
    slots: Optional[List[DeliverySlotInternal]] = None
    updated_at: Optional[datetime] = None

class CustomerSegmentInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    external_id: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_system: Optional[bool] = None
    filters: Optional[CustomerSegmentFilters] = None
    user_ids: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CustomerSegmentInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_system: Optional[bool] = None
    filters: Optional[CustomerSegmentFilters] = None
    user_ids: Optional[List[str]] = None

class CustomerSegmentInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    filters: Optional[CustomerSegmentFilters] = None
    user_ids: Optional[List[str]] = None
    updated_at: Optional[datetime] = None

class CouponQuantityTierInternal(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    min_quantity: Optional[int] = None
    discount_value: Optional[float] = None

class CouponUserUsageInternal(CamelBaseModel):
    user_id: str
    usage_count: int

class CouponInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    external_id: Optional[str] = Field(None, alias="externalId")
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_order_value: Optional[float] = Field(None, alias="min_purchase_amount")
    max_uses: Optional[int] = Field(None, alias="usage_limit")
    used_count: Optional[int] = None
    start_date: Optional[Any] = Field(None, alias="valid_from")
    end_date: Optional[Any] = Field(None, alias="valid_until")
    is_active: Optional[bool] = None
    type_of_discount: Optional[str] = None
    method: Optional[str] = None
    min_requirement_type: Optional[str] = None
    min_quantity_of_eligible_items: Optional[int] = None
    
    max_discount_amount: Optional[float] = None
    applies_to_type: Optional[str] = None
    
    display_id: Optional[str] = None
    buy_x_get_y_customer_gets_applies_to_type: Optional[str] = None
    buy_x_get_y_customer_gets_quantity: Optional[int] = None
    bxgy_applies_to_ids: Optional[Any] = Field(None, alias="buy_x_get_y_customer_gets_applies_to_value_ids")
    bxgy_discount_type: Optional[str] = Field(None, alias="buy_x_get_y_customer_gets_discount_type")
    bxgy_discount_value: Optional[float] = Field(None, alias="buy_x_get_y_customer_gets_discount_value")
    applicable_item_type: Optional[str] = None
    coupon_mode: Optional[str] = None
    max_usage_per_user: Optional[int] = None
    user_usages: Optional[List[CouponUserUsageInternal]] = None
    user_behavior: Optional[str] = None

    
    quantity_tiers: Optional[List[CouponQuantityTierInternal]] = None
    applicable_roles: Optional[List[str]] = None
    applicable_user_ids: Optional[List[str]] = None
    applicable_payment_methods: Optional[List[str]] = None
    shipping_pincodes: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    applies_to_value_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

class CouponInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    used_count: Optional[int] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: Optional[bool] = None
    type_of_discount: Optional[str] = None
    method: Optional[str] = None
    min_requirement_type: Optional[str] = None
    min_quantity_of_eligible_items: Optional[int] = None
    
    max_discount_amount: Optional[float] = None
    applies_to_type: Optional[str] = None
    
    display_id: Optional[str] = None
    buy_x_get_y_customer_gets_applies_to_type: Optional[str] = None
    buy_x_get_y_customer_gets_quantity: Optional[int] = None
    buy_x_get_y_customer_gets_applies_to_value_ids: Optional[List[str]] = None
    buy_x_get_y_customer_gets_discount_type: Optional[str] = None
    buy_x_get_y_customer_gets_discount_value: Optional[float] = None
    applicable_item_type: Optional[str] = None
    coupon_mode: Optional[str] = None
    max_usage_per_user: Optional[int] = None
    user_usages: Optional[List[CouponUserUsageInternal]] = None
    user_behavior: Optional[str] = None

    
    quantity_tiers: Optional[List[CouponQuantityTierInternal]] = None
    applicable_roles: Optional[List[str]] = None
    applicable_user_ids: Optional[List[str]] = None
    applicable_payment_methods: Optional[List[str]] = None
    shipping_pincodes: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    applies_to_value_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None

class CouponInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    used_count: Optional[int] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    is_active: Optional[bool] = None
    type_of_discount: Optional[str] = None
    method: Optional[str] = None
    min_requirement_type: Optional[str] = None
    min_quantity_of_eligible_items: Optional[int] = None
    
    max_discount_amount: Optional[float] = None
    applies_to_type: Optional[str] = None
    
    display_id: Optional[str] = None
    buy_x_get_y_customer_gets_applies_to_type: Optional[str] = None
    buy_x_get_y_customer_gets_quantity: Optional[int] = None
    buy_x_get_y_customer_gets_applies_to_value_ids: Optional[List[str]] = None
    buy_x_get_y_customer_gets_discount_type: Optional[str] = None
    buy_x_get_y_customer_gets_discount_value: Optional[float] = None
    applicable_item_type: Optional[str] = None
    coupon_mode: Optional[str] = None
    max_usage_per_user: Optional[int] = None
    user_usages: Optional[List[CouponUserUsageInternal]] = None
    user_behavior: Optional[str] = None

    
    quantity_tiers: Optional[List[CouponQuantityTierInternal]] = None
    applicable_roles: Optional[List[str]] = None
    applicable_user_ids: Optional[List[str]] = None
    applicable_payment_methods: Optional[List[str]] = None
    shipping_pincodes: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    applies_to_value_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None

class PromoStripsInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    is_active: Optional[bool] = None
    text: Optional[str] = None
    zone_ids: Optional[List[str]] = None

class PromoStripsInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    is_active: Optional[bool] = None
    text: Optional[str] = None
    zone_ids: Optional[List[str]] = None

class PushNotificationsInternal(CamelBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    title: Optional[str] = None
    message: Optional[str] = None
    link: Optional[str] = None
    image: Optional[str] = None
    status: Optional[str] = None
    scheduled_for: Optional[str] = None
    delivered_count: Optional[int] = None
    read_count: Optional[int] = None
    user_segment: Optional[str] = None
    user_behavior: Optional[str] = None
    created_by: Optional[str] = None
    targetedUserIds: Optional[List[str]] = None
    readByUserIds: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PushNotificationsInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    created_by: Optional[str] = None
    delivered_count: Optional[int] = None
    image: Optional[str] = None
    link: Optional[str] = None
    message: Optional[str] = None
    read_count: Optional[int] = None
    scheduled_for: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None
    user_segment: Optional[str] = None
    user_behavior: Optional[str] = None

    user_segment: Optional[str] = None
    user_behavior: Optional[str] = None
    user_behavior: Optional[str] = None
    user_segment: Optional[str] = None

class PushNotificationsInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    created_by: Optional[str] = None
    delivered_count: Optional[int] = None
    image: Optional[str] = None
    link: Optional[str] = None
    message: Optional[str] = None
    read_count: Optional[int] = None
    scheduled_for: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None
    user_behavior: Optional[str] = None
    user_segment: Optional[str] = None

class CoachMarksInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    anchor_id: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    title: Optional[str] = None

class CoachMarksInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    anchor_id: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    title: Optional[str] = None

class CategoryTagsInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    description: Optional[str] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None

class CategoryTagsInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    description: Optional[str] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None

class Google_reviewsInternal(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    id: Optional[str] = Field(None, alias="_id")
    external_id: Optional[str] = None
    lastUpdated: Optional[str] = None
    method: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Google_reviewsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    lastUpdated: Optional[str] = None
    method: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[int] = None

class Google_reviewsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    lastUpdated: Optional[str] = None
    method: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[int] = None

class StockReservationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    expires_at: Optional[str] = None
    product_id: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    user_id: Optional[str] = None

class StockReservationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    expires_at: Optional[str] = None
    product_id: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    user_id: Optional[str] = None

class ProductNotificationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    email: Optional[str] = None
    phone: Optional[str] = None
    product_id: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[str] = None

class ProductNotificationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    email: Optional[str] = None
    phone: Optional[str] = None
    product_id: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[str] = None

class ProductReviewsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    product_id: Optional[str] = None
    rating: Optional[int] = None
    reviewText: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[str] = None
    userName: Optional[str] = Field(None, alias='userName')
    classification: Optional[str] = None

class ProductReviewsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    product_id: Optional[str] = None
    rating: Optional[int] = None
    reviewText: Optional[str] = None
    status: Optional[str] = None
    userName: Optional[str] = Field(None, alias='userName')
    classification: Optional[str] = None
    user_id: Optional[str] = None

class ClassificationTagsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    is_active: Optional[bool] = None
    name: Optional[str] = None

class ClassificationTagsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    is_active: Optional[bool] = None
    name: Optional[str] = None

class ReviewClassificationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    category: Optional[str] = None
    confidenceScore: Optional[float] = None
    reviewId: Optional[str] = None
    sentiment: Optional[str] = None

class ReviewClassificationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    category: Optional[str] = None
    confidenceScore: Optional[float] = None
    reviewId: Optional[str] = None
    sentiment: Optional[str] = None

class AboutUsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    content: Optional[str] = None
    isPublished: Optional[bool] = None
    title: Optional[str] = None
    version: Optional[str] = None

class AboutUsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    content: Optional[str] = None
    isPublished: Optional[bool] = None
    title: Optional[str] = None
    version: Optional[str] = None

class PrivacyPolicyInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    content: Optional[str] = None
    effectiveDate: Optional[str] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None

class PrivacyPolicyInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    content: Optional[str] = None
    effectiveDate: Optional[str] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None

class AvailabilityRequestsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    pincode: Optional[str] = None
    product_id: Optional[str] = None
    productName: Optional[str] = None
    userEmail: Optional[str] = None
    userName: Optional[str] = None

class AvailabilityRequestsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    pincode: Optional[str] = None
    product_id: Optional[str] = None
    productName: Optional[str] = None
    userEmail: Optional[str] = None
    userName: Optional[str] = None

class PincodeSearchesInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    isServiceable: Optional[bool] = None
    pincode: Optional[str] = None
    query: Optional[str] = None
    timestamp: Optional[str] = None

class PincodeSearchesInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    isServiceable: Optional[bool] = None
    pincode: Optional[str] = None
    query: Optional[str] = None
    timestamp: Optional[str] = None

class SystemSettingsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    allowSignups: Optional[bool] = None
    defaultCurrency: Optional[str] = None
    maintenanceMode: Optional[bool] = None
    maxUploadSizeMb: Optional[int] = None
    timezone: Optional[str] = None

class SystemSettingsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    allowSignups: Optional[bool] = None
    defaultCurrency: Optional[str] = None
    maintenanceMode: Optional[bool] = None
    maxUploadSizeMb: Optional[int] = None
    timezone: Optional[str] = None

class ValetPayoutSettingsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    deliveryChargePerOrder: Optional[float] = None
    returnPickupChargePerOrder: Optional[float] = None

class ValetPayoutSettingsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    deliveryChargePerOrder: Optional[float] = None
    returnPickupChargePerOrder: Optional[float] = None

class SupportTicketInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    ticket_number: str
    user: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = "general"
    priority: Optional[str] = "medium"
    status: Optional[str] = "open"
    attachments: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    responses: Optional[List[TicketResponseItemInternal]] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    created_at: Optional[datetime] = None

class SupportTicketInternalUpdate(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    external_id: Optional[str] = Field(None, alias='externalId')
    assigned_to: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    responses: Optional[List[TicketResponseItemInternal]] = None

from app.models.schemas import TicketResponseItem

class ActivityMetaInternal(BaseModel):
    key: str
    value: str

class ActivityInternalCreate(CamelBaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    action: str
    comments: Optional[str] = None
    is_guest: Optional[bool] = None
    user_agent: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    device_type: Optional[str] = None
    meta: Optional[List[ActivityMetaInternal]] = None

class ActivityInternalUpdate(CamelBaseModel):
    user_id: Optional[str] = None
    is_guest: Optional[bool] = None
    comments: Optional[str] = None

from app.models.base import CamelBaseModel
class ActivityInternal(CamelBaseModel):
    id: str = Field(alias="_id")
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    action: str
    comments: Optional[str] = None
    is_guest: Optional[bool] = None
    user_agent: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    device_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    meta: Optional[List[ActivityMetaInternal]] = None

class ReturnRequestItemInternal(CamelBaseModel):
    product_id: str
    quantity: int
    reason: Optional[str] = None

class ReturnRequestValetDeclineInternal(CamelBaseModel):
    valet_id: str
    reason: Optional[str] = None

class ReturnRequestInternal(CamelBaseModel):
    id: str = Field(alias="_id")
    return_id: Optional[str] = None
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    payment_method: Optional[str] = None
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    valet_id: Optional[str] = None
    seller_id: Optional[str] = None
    delivery_slot_id: Optional[str] = None
    delivery_slot_config_id: Optional[str] = None
    delivery_slot_date: Optional[str] = None
    pending_valet_id: Optional[str] = None
    valet_assigned_at: Optional[str] = None
    valet_cascade_count: Optional[int] = None
    delivery_charge: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: Optional[List[ReturnRequestItemInternal]] = None
    valet_decline_history: Optional[List[ReturnRequestValetDeclineInternal]] = None
    notes: Optional[str] = None

class ReturnRequestInternalCreate(CamelBaseModel):
    return_id: Optional[str] = None
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    payment_method: Optional[str] = None
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    valet_id: Optional[str] = None
    seller_id: Optional[str] = None
    delivery_slot_id: Optional[str] = None
    delivery_slot_config_id: Optional[str] = None
    delivery_slot_date: Optional[str] = None
    pending_valet_id: Optional[str] = None
    valet_assigned_at: Optional[str] = None
    valet_cascade_count: Optional[int] = None
    delivery_charge: Optional[float] = None
    items: Optional[List[ReturnRequestItemInternal]] = None
    valet_decline_history: Optional[List[ReturnRequestValetDeclineInternal]] = None
    notes: Optional[str] = None

class ReturnRequestInternalUpdate(CamelBaseModel):
    status: Optional[str] = None
    valet_id: Optional[str] = None
    pending_valet_id: Optional[str] = None
    valet_assigned_at: Optional[str] = None
    valet_cascade_count: Optional[int] = None
    valet_decline_history: Optional[List[ReturnRequestValetDeclineInternal]] = None
    notes: Optional[str] = None


class SellerAvailabilityInternalCreate(CamelBaseModel):
    model_config = ConfigDict(extra="forbid")
    seller_id: Optional[str] = None
    status: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    is_full_day: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

