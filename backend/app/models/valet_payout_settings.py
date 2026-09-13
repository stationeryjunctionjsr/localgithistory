from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import Field
from pydantic import BaseModel

class ValetPayoutSettings(BaseModel):
    id: str = Field(default=None, alias='_id')
    external_id: Optional[str] = Field(default=None, alias='external_id')
    delivery_charge_per_order: float = Field(default=0.0, alias='deliveryChargePerOrder')
    return_pickup_charge_per_order: float = Field(default=0.0, alias='returnPickupChargePerOrder')
    created_at: Optional[datetime] = Field(default=None, alias='createdAt')
    updated_at: Optional[datetime] = Field(default=None, alias='updatedAt')
    eid: Optional[str] = Field(default=None, alias='eid')
    c: Optional[str] = Field(default=None, alias='c')
    u: Optional[str] = Field(default=None, alias='u')
    return_settings: Optional[Dict] = Field(default=None, alias='returnSettings')
    order_feedback: Optional[str] = Field(default=None, alias='orderFeedback')
    promo_strips: Optional[str] = Field(default=None, alias='promoStrips')
    push_notifications: Optional[str] = Field(default=None, alias='pushNotifications')
    coach_marks: Optional[str] = Field(default=None, alias='coachMarks')
    category_tags: Optional[Dict] = Field(default=None, alias='categoryTags')
    google_reviews: int = Field(default=0, alias='google_reviews')
    stock_reservations: Optional[str] = Field(default=None, alias='stockReservations')
    product_notifications: Optional[str] = Field(default=None, alias='productNotifications')
    product_reviews: int = Field(default=0, alias='productReviews')
    classification_tags: Optional[Dict] = Field(default=None, alias='classificationTags')
    review_classifications: Optional[str] = Field(default=None, alias='reviewClassifications')
    about_us: Optional[str] = Field(default=None, alias='aboutUs')
    privacy_policy: Optional[str] = Field(default=None, alias='privacyPolicy')
    availability_requests: Optional[str] = Field(default=None, alias='availabilityRequests')
    pincode_searches: Optional[str] = Field(default=None, alias='pincodeSearches')
    system_settings: Optional[Dict] = Field(default=None, alias='systemSettings')
    valet_payout_settings: Optional[Dict] = Field(default=None, alias='valetPayoutSettings')
