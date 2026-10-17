from app.models.base import CamelBaseModel
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel
from typing import Any, Optional, List
from datetime import datetime, timezone
from app.models.schemas import TicketResponseItemInternal, SocialMedia
from app.models.daos import CustomerSegmentFilters

class FlatCamelBaseModel(CamelBaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra='forbid',
        from_attributes=True,
    )

class ReturnSettingsInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    return_days: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ReturnSettingsInternalCreate(FlatCamelBaseModel):
    return_days: Optional[int] = None

class ReturnSettingsInternalUpdate(FlatCamelBaseModel):
    return_days: Optional[int] = None

class SchemeInternal(FlatCamelBaseModel):
    id: Optional[int] = None
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

class SchemeInternalCreate(FlatCamelBaseModel):
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

class SchemeInternalUpdate(FlatCamelBaseModel):
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

class ContactInternal(FlatCamelBaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    addresses: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    social_media: Optional[SocialMedia] = None

class ContactInternalCreate(FlatCamelBaseModel):
    email: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    addresses: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None
    social_media: Optional[SocialMedia] = None

class ContactInternalUpdate(FlatCamelBaseModel):
    email: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    addresses: Optional[List[str]] = None
    phone_numbers: Optional[List[str]] = None
    social_media: Optional[SocialMedia] = None

class OrderFeedbackInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    comment: Optional[str] = None
    delivery_comment: Optional[str] = None
    delivery_rating: Optional[int] = None
    feedback_type: Optional[str] = None
    order_id: Optional[str] = None
    rating: Optional[int] = None
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class OrderFeedbackInternalCreate(FlatCamelBaseModel):
    comment: Optional[str] = None
    delivery_comment: Optional[str] = None
    delivery_rating: Optional[int] = None
    feedback_type: Optional[str] = None
    order_id: Optional[str] = None
    rating: Optional[int] = None
    user_id: Optional[str] = None

class OrderFeedbackInternalUpdate(FlatCamelBaseModel):
    comment: Optional[str] = None
    delivery_comment: Optional[str] = None
    delivery_rating: Optional[int] = None
    feedback_type: Optional[str] = None
    order_id: Optional[str] = None
    rating: Optional[int] = None
    user_id: Optional[str] = None

class PromoStripsInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    is_active: Optional[bool] = None
    text: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    zone_ids: Optional[List[int]] = None

class DeviceKeyInternal(FlatCamelBaseModel):
    key: str
    value: str

class DeviceSubscriptionInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    endpoint: Optional[str] = None
    expo_token: Optional[str] = None
    keys: Optional[List[DeviceKeyInternal]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DeviceSubscriptionInternalCreate(FlatCamelBaseModel):
    user_id: Optional[int] = None
    endpoint: Optional[str] = None
    expo_token: Optional[str] = None
    keys: Optional[List[DeviceKeyInternal]] = None

class DeviceSubscriptionInternalUpdate(FlatCamelBaseModel):
    user_id: Optional[int] = None
    endpoint: Optional[str] = None
    expo_token: Optional[str] = None
    keys: Optional[List[DeviceKeyInternal]] = None

class CollectionInternal(FlatCamelBaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    visible_pages: Optional[List[str]] = None
    user_segments: Optional[List[str]] = None
    visibility_rules: Optional[List[str]] = None
    product_ids: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CollectionInternalCreate(FlatCamelBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    visible_pages: Optional[List[str]] = None
    user_segments: Optional[List[str]] = None
    visibility_rules: Optional[List[str]] = None
    product_ids: Optional[List[str]] = None

class CollectionInternalUpdate(FlatCamelBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    visible_pages: Optional[List[str]] = None
    user_segments: Optional[List[str]] = None
    visibility_rules: Optional[List[str]] = None
    product_ids: Optional[List[str]] = None

class SearchTagInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    tag_id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    categories: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    product_ids: Optional[List[int]] = None
    excluded_product_ids: Optional[List[int]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SearchTagInternalCreate(FlatCamelBaseModel):
    tag_id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    categories: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    product_ids: Optional[List[int]] = None
    excluded_product_ids: Optional[List[int]] = None

class SearchTagInternalUpdate(FlatCamelBaseModel):
    tag_id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    categories: Optional[List[str]] = None
    sub_categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    product_ids: Optional[List[int]] = None
    excluded_product_ids: Optional[List[int]] = None

class CoachMarkInternal(FlatCamelBaseModel):
    id: Optional[str] = None
    anchor_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CoachMarkInternalCreate(FlatCamelBaseModel):
    anchor_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    is_active: Optional[bool] = None

class CoachMarkInternalUpdate(FlatCamelBaseModel):
    anchor_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    is_active: Optional[bool] = None

class CategoryTagInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    division_id: Optional[int] = None
    division_name: Optional[str] = None
    category_head_id: Optional[int] = None
    category_head_name: Optional[str] = None
    category_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CategoryTagInternalCreate(FlatCamelBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    division_id: Optional[int] = None
    category_head_id: Optional[int] = None

class CategoryTagInternalUpdate(FlatCamelBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    division_id: Optional[int] = None
    category_head_id: Optional[int] = None

class DeliveryChargeTierInternal(FlatCamelBaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    charge: Optional[float] = None

class DeliveryChargeInternal(FlatCamelBaseModel):
    id: Optional[int] = None
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

class DeliveryChargeInternalCreate(FlatCamelBaseModel):
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

class DeliveryChargeInternalUpdate(FlatCamelBaseModel):
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

class DeliveryChargeDefaultInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    applicable_to_wholesaler: Optional[bool] = None
    applicable_to_retailer: Optional[bool] = None
    charge: Optional[float] = None
    urgent_delivery_available: Optional[bool] = None
    urgent_delivery_charge: Optional[float] = None
    courier_base_charge: Optional[float] = None
    courier_free_threshold: Optional[float] = None
    hyperlocal_base_charge: Optional[float] = None
    hyperlocal_free_threshold: Optional[float] = None
    hyperlocal_urgent_delivery_charge: Optional[float] = None
    is_active: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DeliveryChargeDefaultInternalCreate(FlatCamelBaseModel):
    applicable_to_wholesaler: Optional[bool] = None
    applicable_to_retailer: Optional[bool] = None
    charge: Optional[float] = None
    urgent_delivery_available: Optional[bool] = None
    urgent_delivery_charge: Optional[float] = None
    courier_base_charge: Optional[float] = None
    courier_free_threshold: Optional[float] = None
    hyperlocal_base_charge: Optional[float] = None
    hyperlocal_free_threshold: Optional[float] = None
    hyperlocal_urgent_delivery_charge: Optional[float] = None
    is_active: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliveryChargeDefaultInternalUpdate(FlatCamelBaseModel):
    applicable_to_wholesaler: Optional[bool] = None
    applicable_to_retailer: Optional[bool] = None
    charge: Optional[float] = None
    urgent_delivery_available: Optional[bool] = None
    urgent_delivery_charge: Optional[float] = None
    courier_base_charge: Optional[float] = None
    courier_free_threshold: Optional[float] = None
    hyperlocal_base_charge: Optional[float] = None
    hyperlocal_free_threshold: Optional[float] = None
    hyperlocal_urgent_delivery_charge: Optional[float] = None
    is_active: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliveryZoneInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    default_capacity: Optional[int] = None
    urgent_delivery_available: Optional[bool] = None
    customer_type: Optional[str] = None
    is_active: Optional[bool] = None
    delivery_charge: Optional[float] = None
    min_cart_value: Optional[float] = None
    urgent_delivery_charge: Optional[float] = None
    apply_default_charge: Optional[bool] = True
    pincodes: Optional[List[str]] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DeliveryZoneInternalCreate(FlatCamelBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_capacity: Optional[int] = None
    urgent_delivery_available: Optional[bool] = None
    customer_type: Optional[str] = None
    is_active: Optional[bool] = None
    delivery_charge: Optional[float] = None
    min_cart_value: Optional[float] = None
    urgent_delivery_charge: Optional[float] = None
    apply_default_charge: Optional[bool] = True
    pincodes: Optional[List[str]] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliveryZoneInternalUpdate(FlatCamelBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_capacity: Optional[int] = None
    urgent_delivery_available: Optional[bool] = None
    customer_type: Optional[str] = None
    is_active: Optional[bool] = None
    delivery_charge: Optional[float] = None
    min_cart_value: Optional[float] = None
    urgent_delivery_charge: Optional[float] = None
    apply_default_charge: Optional[bool] = None
    pincodes: Optional[List[str]] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliverySlotInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    capacity: Optional[int] = None
    booked_count: Optional[int] = 0
    is_full_day: Optional[bool] = False
    is_urgent: Optional[bool] = False
    cutoff_hours: Optional[int] = None
    urgent_cutoff_hours: Optional[int] = None
    is_active: Optional[bool] = True

class DeliverySlotConfigInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    segment: Optional[str] = None
    date: Optional[str] = None
    zone_id: Optional[str] = None
    is_active: Optional[bool] = None
    slots: Optional[List[DeliverySlotInternal]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DeliverySlotConfigInternalCreate(FlatCamelBaseModel):
    segment: Optional[str] = None
    date: Optional[str] = None
    zone_id: Optional[str] = None
    is_active: Optional[bool] = None
    slots: Optional[List[DeliverySlotInternal]] = None

class DeliverySlotConfigInternalUpdate(FlatCamelBaseModel):
    segment: Optional[str] = None
    date: Optional[str] = None
    zone_id: Optional[str] = None
    is_active: Optional[bool] = None
    slots: Optional[List[DeliverySlotInternal]] = None
    updated_at: Optional[datetime] = None

class CustomerSegmentInternal(FlatCamelBaseModel):
    id: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_system: Optional[bool] = None
    filters: Optional[CustomerSegmentFilters] = None
    user_ids: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CustomerSegmentInternalCreate(FlatCamelBaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_system: Optional[bool] = None
    filters: Optional[CustomerSegmentFilters] = None
    user_ids: Optional[List[str]] = None

class CustomerSegmentInternalUpdate(FlatCamelBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    filters: Optional[CustomerSegmentFilters] = None
    user_ids: Optional[List[str]] = None
    updated_at: Optional[datetime] = None

class CouponQuantityTierInternal(FlatCamelBaseModel):
    min_quantity: Optional[int] = None
    discount_value: Optional[float] = None

class CouponUserUsageInternal(FlatCamelBaseModel):
    user_id: str
    usage_count: int

class CouponInternal(FlatCamelBaseModel):
    id: Optional[str] = None
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_order_value: Optional[float] = Field(None, alias="min_purchase_amount")
    max_uses: Optional[int] = Field(None, alias="usage_limit")
    used_count: Optional[int] = None
    start_date: Optional[datetime] = Field(None, alias="valid_from")
    end_date: Optional[datetime] = Field(None, alias="valid_until")
    is_active: Optional[bool] = None
    type_of_discount: Optional[str] = None
    method: Optional[str] = None
    min_requirement_type: Optional[str] = None
    min_quantity_of_eligible_items: Optional[int] = None
    
    max_discount_amount: Optional[float] = None
    applies_to_type: Optional[str] = None
    
    display_id: Optional[str] = None
    buy_x_get_y_customer_gets_applies_to_type: Optional[str] = Field(None, alias="bxgy_customer_gets_applies_to_type")
    buy_x_get_y_customer_gets_quantity: Optional[int] = Field(None, alias="bxgy_customer_gets_quantity")
    bxgy_applies_to_ids: Optional[List[str]] = Field(None, alias="buy_x_get_y_customer_gets_applies_to_value_ids")
    bxgy_discount_type: Optional[str] = Field(None, alias="buy_x_get_y_customer_gets_discount_type")
    bxgy_discount_value: Optional[float] = Field(None, alias="buy_x_get_y_customer_gets_discount_value")
    applicable_item_type: Optional[str] = None
    coupon_mode: Optional[str] = None
    max_usage_per_user: Optional[int] = None
    user_usages: Optional[List[CouponUserUsageInternal]] = None
    user_behavior: Optional[str] = None

    quantity_tiers: Optional[List[CouponQuantityTierInternal]] = None

    @field_validator('applies_to_ids', 'bxgy_applies_to_ids', 'bxgy_customer_gets_applies_to_ids', 'applicable_payment_methods', mode='before', check_fields=False)
    @classmethod
    def parse_json_lists(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return []
        return v

    applicable_roles: Optional[List[str]] = None
    applicable_user_ids: Optional[List[str]] = None
    applicable_payment_methods: Optional[List[str]] = None
    shipping_pincodes: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    applies_to_value_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CouponInternalCreate(FlatCamelBaseModel):
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    used_count: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    @field_validator('valid_from', 'valid_until', mode='after')
    @classmethod
    def ensure_naive_utc(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v

    is_active: Optional[bool] = None
    type_of_discount: Optional[str] = None
    method: Optional[str] = None
    min_requirement_type: Optional[str] = None
    min_quantity_of_eligible_items: Optional[int] = None
    
    max_discount_amount: Optional[float] = None
    applies_to_type: Optional[str] = None
    
    display_id: Optional[str] = None
    buy_x_get_y_customer_gets_applies_to_type: Optional[str] = Field(None, alias="bxgy_customer_gets_applies_to_type")
    buy_x_get_y_customer_gets_quantity: Optional[int] = Field(None, alias="bxgy_customer_gets_quantity")
    buy_x_get_y_customer_gets_applies_to_value_ids: Optional[List[str]] = None
    buy_x_get_y_customer_gets_discount_type: Optional[str] = None
    buy_x_get_y_customer_gets_discount_value: Optional[float] = None
    applicable_item_type: Optional[str] = None
    coupon_mode: Optional[str] = None
    max_usage_per_user: Optional[int] = None
    user_usages: Optional[List[CouponUserUsageInternal]] = None
    user_behavior: Optional[str] = None

    quantity_tiers: Optional[List[CouponQuantityTierInternal]] = None

    @field_validator('applies_to_ids', 'bxgy_applies_to_ids', 'bxgy_customer_gets_applies_to_ids', mode='before', check_fields=False)
    @classmethod
    def parse_json_lists(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return []
        return v

    applicable_roles: Optional[List[str]] = None
    applicable_user_ids: Optional[List[str]] = None
    applicable_payment_methods: Optional[List[str]] = None
    shipping_pincodes: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    applies_to_value_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None

class CouponInternalUpdate(FlatCamelBaseModel):
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    used_count: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    @field_validator('valid_from', 'valid_until', mode='after')
    @classmethod
    def ensure_naive_utc(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None and v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v

    is_active: Optional[bool] = None
    type_of_discount: Optional[str] = None
    method: Optional[str] = None
    min_requirement_type: Optional[str] = None
    min_quantity_of_eligible_items: Optional[int] = None
    
    max_discount_amount: Optional[float] = None
    applies_to_type: Optional[str] = None
    
    display_id: Optional[str] = None
    buy_x_get_y_customer_gets_applies_to_type: Optional[str] = Field(None, alias="bxgy_customer_gets_applies_to_type")
    buy_x_get_y_customer_gets_quantity: Optional[int] = Field(None, alias="bxgy_customer_gets_quantity")
    buy_x_get_y_customer_gets_applies_to_value_ids: Optional[List[str]] = None
    buy_x_get_y_customer_gets_discount_type: Optional[str] = None
    buy_x_get_y_customer_gets_discount_value: Optional[float] = None
    applicable_item_type: Optional[str] = None
    coupon_mode: Optional[str] = None
    max_usage_per_user: Optional[int] = None
    user_usages: Optional[List[CouponUserUsageInternal]] = None
    user_behavior: Optional[str] = None

    quantity_tiers: Optional[List[CouponQuantityTierInternal]] = None

    @field_validator('applies_to_ids', 'bxgy_applies_to_ids', 'bxgy_customer_gets_applies_to_ids', mode='before', check_fields=False)
    @classmethod
    def parse_json_lists(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return []
        return v

    applicable_roles: Optional[List[str]] = None
    applicable_user_ids: Optional[List[str]] = None
    applicable_payment_methods: Optional[List[str]] = None
    shipping_pincodes: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    applies_to_value_ids: Optional[List[str]] = None
    excluded_product_ids: Optional[List[str]] = None

class CouponOverlapDetail(FlatCamelBaseModel):
    coupon_id: str
    display_id: str
    overlapping_product_ids: List[str]

class CouponOverlapData(FlatCamelBaseModel):
    total_overlapping_products: int
    details: List[CouponOverlapDetail]

class PromoStripsInternalCreate(FlatCamelBaseModel):
    is_active: Optional[bool] = None
    text: Optional[str] = None
    zone_ids: Optional[List[int]] = None

class PromoStripsInternalUpdate(FlatCamelBaseModel):
    is_active: Optional[bool] = None
    text: Optional[str] = None
    zone_ids: Optional[List[int]] = None

class PushNotificationsInternal(FlatCamelBaseModel):
    id: Optional[int] = None
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

class PushNotificationsInternalCreate(FlatCamelBaseModel):
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

class PushNotificationsInternalUpdate(FlatCamelBaseModel):
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

class CoachMarksInternalCreate(FlatCamelBaseModel):
    anchor_id: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    title: Optional[str] = None

class CoachMarksInternalUpdate(FlatCamelBaseModel):
    anchor_id: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    screen_name: Optional[str] = None
    sequence_order: Optional[int] = None
    title: Optional[str] = None

class CategoryTagsInternalCreate(FlatCamelBaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None
    division_id: Optional[int] = None
    category_head_id: Optional[int] = None

class CategoryTagsInternalUpdate(FlatCamelBaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None
    division_id: Optional[int] = None
    category_head_id: Optional[int] = None

class Google_reviewsInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    lastUpdated: Optional[str] = None
    method: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Google_reviewsInternalCreate(FlatCamelBaseModel):
    lastUpdated: Optional[str] = None
    method: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[str] = None

class Google_reviewsInternalUpdate(FlatCamelBaseModel):
    lastUpdated: Optional[str] = None
    method: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[str] = None

class StockReservationsInternalCreate(FlatCamelBaseModel):
    expires_at: Optional[str] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    user_id: Optional[str] = None

class StockReservationsInternalUpdate(FlatCamelBaseModel):
    expires_at: Optional[str] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    user_id: Optional[str] = None


class ProductNotificationsInternal(CamelBaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    product_id: int
    status: Optional[str] = "active"
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProductNotificationsInternalCreate(FlatCamelBaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    product_id: Optional[int] = None
    status: Optional[str] = None
    user_id: Optional[str] = None

class ProductNotificationsInternalUpdate(FlatCamelBaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    product_id: Optional[int] = None
    status: Optional[str] = None
    user_id: Optional[str] = None

class ProductReviewsInternalCreate(FlatCamelBaseModel):
    product_id: Optional[int] = None
    rating: Optional[int] = None
    review_text: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    classification: Optional[str] = None

class ProductReviewsInternalUpdate(FlatCamelBaseModel):
    product_id: Optional[int] = None
    rating: Optional[int] = None
    review_text: Optional[str] = None
    status: Optional[str] = None
    user_name: Optional[str] = None
    classification: Optional[str] = None
    user_id: Optional[int] = None

class ClassificationTagsInternalCreate(FlatCamelBaseModel):
    is_active: Optional[bool] = None
    name: Optional[str] = None

class ClassificationTagsInternalUpdate(FlatCamelBaseModel):
    is_active: Optional[bool] = None
    name: Optional[str] = None

class ReviewClassificationsInternalCreate(FlatCamelBaseModel):
    category: Optional[str] = None
    confidence_score: Optional[float] = None
    review_id: Optional[str] = None
    sentiment: Optional[str] = None

class ReviewClassificationsInternalUpdate(FlatCamelBaseModel):
    category: Optional[str] = None
    confidence_score: Optional[float] = None
    review_id: Optional[str] = None
    sentiment: Optional[str] = None

class AboutUsInternalCreate(FlatCamelBaseModel):
    content: Optional[str] = None
    is_published: Optional[bool] = None
    title: Optional[str] = None
    version: Optional[str] = None

class AboutUsInternalUpdate(FlatCamelBaseModel):
    content: Optional[str] = None
    is_published: Optional[bool] = None
    title: Optional[str] = None
    version: Optional[str] = None

class PrivacyPolicyInternalCreate(FlatCamelBaseModel):
    content: Optional[str] = None
    effective_date: Optional[str] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None

class PrivacyPolicyInternalUpdate(FlatCamelBaseModel):
    content: Optional[str] = None
    effective_date: Optional[str] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None

class AvailabilityRequestsInternalCreate(FlatCamelBaseModel):
    pincode: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None

class AvailabilityRequestsInternalUpdate(FlatCamelBaseModel):
    pincode: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None

class PincodeSearchesInternalCreate(FlatCamelBaseModel):
    is_serviceable: Optional[bool] = None
    pincode: Optional[str] = None
    query: Optional[str] = None
    timestamp: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None

class PincodeSearchesInternalUpdate(FlatCamelBaseModel):
    is_serviceable: Optional[bool] = None
    pincode: Optional[str] = None
    query: Optional[str] = None
    timestamp: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None

class SystemSettingsInternalCreate(FlatCamelBaseModel):
    allow_signups: Optional[bool] = None
    default_currency: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    max_upload_size_mb: Optional[int] = None
    timezone: Optional[str] = None

class SystemSettingsInternalUpdate(FlatCamelBaseModel):
    allow_signups: Optional[bool] = None
    default_currency: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    max_upload_size_mb: Optional[int] = None
    timezone: Optional[str] = None

class ValetPayoutSettingsInternalCreate(FlatCamelBaseModel):
    delivery_charge_per_order: Optional[float] = None
    return_pickup_charge_per_order: Optional[float] = None

class ValetPayoutSettingsInternalUpdate(FlatCamelBaseModel):
    delivery_charge_per_order: Optional[float] = None
    return_pickup_charge_per_order: Optional[float] = None

class SupportTicketInternalCreate(FlatCamelBaseModel):
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

class SupportTicketInternalUpdate(FlatCamelBaseModel):
    ticket_number: Optional[str] = None
    user: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    attachments: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    responses: Optional[List[TicketResponseItemInternal]] = None

from app.models.schemas import TicketResponseItem

class ActivityMetaInternal(FlatCamelBaseModel):
    key: str
    value: str

class ActivityInternalCreate(FlatCamelBaseModel):
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

class ActivityInternalUpdate(FlatCamelBaseModel):
    user_id: Optional[str] = None
    is_guest: Optional[bool] = None
    comments: Optional[str] = None

class ActivityInternal(FlatCamelBaseModel):
    id: Optional[str] = None
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

    @property
    def userId(self) -> Optional[str]:
        return self.user_id

class ReturnRequestItemInternal(FlatCamelBaseModel):
    product_id: int
    quantity: int
    reason: Optional[str] = None

class ReturnRequestValetDeclineInternal(FlatCamelBaseModel):
    valet_id: str
    reason: Optional[str] = None

class ReturnRequestInternal(FlatCamelBaseModel):
    id: Optional[int] = None
    return_id: Optional[str] = None
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    payment_method: Optional[str] = None
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    valet_id: Optional[str] = None
    seller_id: Optional[int] = None
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


class ReturnRequestInternalCreate(FlatCamelBaseModel):
    id: Optional[int] = None
    return_id: Optional[str] = None
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    payment_method: Optional[str] = None
    upi_payment_screenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    valet_id: Optional[str] = None
    seller_id: Optional[int] = None
    delivery_slot_id: Optional[str] = None
    delivery_slot_config_id: Optional[str] = None
    delivery_slot_date: Optional[str] = None
    pending_valet_id: Optional[str] = None
    valet_assigned_at: Optional[str] = None
    valet_cascade_count: Optional[int] = None
    delivery_charge: Optional[float] = None
    items: Optional[List[ReturnRequestItemInternal]] = None
    valet_decline_history: Optional[List[ReturnRequestValetDeclineInternal]] = None


class ReturnRequestInternalUpdate(FlatCamelBaseModel):
    status: Optional[str] = None
    valet_id: Optional[str] = None
    pending_valet_id: Optional[str] = None
    valet_assigned_at: Optional[str] = None
    valet_cascade_count: Optional[int] = None
    items: Optional[List[ReturnRequestItemInternal]] = None
    valet_decline_history: Optional[List[ReturnRequestValetDeclineInternal]] = None
    notes: Optional[str] = None

class SellerAvailabilityInternalCreate(FlatCamelBaseModel):
    seller_id: Optional[int] = None
    status: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    reason: Optional[str] = None
    created_by: Optional[str] = None
    cancelled_at: Optional[str] = None
    is_full_day: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SellerAvailabilityInternalUpdate(FlatCamelBaseModel):
    seller_id: Optional[int] = None
    status: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    reason: Optional[str] = None
    created_by: Optional[str] = None
    cancelled_at: Optional[str] = None
    updated_at: Optional[datetime] = None

class SellerAvailabilityFilter(FlatCamelBaseModel):
    id: Optional[int] = None
    seller_id: Optional[int] = None
    status: Optional[str] = None
    statuses: Optional[List[str]] = None


from app.models.product import Product
from app.models.bundle import Bundle

ProductInternal = Product
BundleInternal = Bundle

