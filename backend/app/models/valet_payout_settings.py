from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from app.models.core import DictCompatibleModel

class ValetPayoutSettings(DictCompatibleModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[Any] = Field(default=None, alias='external_id')
    delivery_charge_per_order: Optional[Any] = Field(default=None, alias='deliveryChargePerOrder')
    return_pickup_charge_per_order: Optional[Any] = Field(default=None, alias='returnPickupChargePerOrder')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[Any] = Field(default=None, alias='eid')
    c: Optional[Any] = Field(default=None, alias='c')
    u: Optional[Any] = Field(default=None, alias='u')
    return_settings: Optional[Any] = Field(default=None, alias='returnSettings')
    order_feedback: Optional[Any] = Field(default=None, alias='orderFeedback')
    promo_strips: Optional[Any] = Field(default=None, alias='promoStrips')
    push_notifications: Optional[Any] = Field(default=None, alias='pushNotifications')
    coach_marks: Optional[Any] = Field(default=None, alias='coachMarks')
    category_tags: Optional[Any] = Field(default=None, alias='categoryTags')
    google_reviews: Optional[Any] = Field(default=None, alias='google_reviews')
    stock_reservations: Optional[Any] = Field(default=None, alias='stockReservations')
    product_notifications: Optional[Any] = Field(default=None, alias='productNotifications')
    product_reviews: Optional[Any] = Field(default=None, alias='productReviews')
    classification_tags: Optional[Any] = Field(default=None, alias='classificationTags')
    review_classifications: Optional[Any] = Field(default=None, alias='reviewClassifications')
    about_us: Optional[Any] = Field(default=None, alias='aboutUs')
    privacy_policy: Optional[Any] = Field(default=None, alias='privacyPolicy')
    availability_requests: Optional[Any] = Field(default=None, alias='availabilityRequests')
    pincode_searches: Optional[Any] = Field(default=None, alias='pincodeSearches')
    system_settings: Optional[Any] = Field(default=None, alias='systemSettings')
    valet_payout_settings: Optional[Any] = Field(default=None, alias='valetPayoutSettings')
