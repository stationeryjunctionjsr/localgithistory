from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Dict, List

class ReturnSettingsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    returnDays: Optional[Any] = None

class ReturnSettingsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    returnDays: Optional[Any] = None

class OrderFeedbackInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    comment: Optional[Any] = None
    deliveryComment: Optional[Any] = None
    deliveryRating: Optional[Any] = None
    feedbackType: Optional[Any] = None
    orderId: Optional[Any] = None
    rating: Optional[Any] = None
    userId: Optional[Any] = None

class OrderFeedbackInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    comment: Optional[Any] = None
    deliveryComment: Optional[Any] = None
    deliveryRating: Optional[Any] = None
    feedbackType: Optional[Any] = None
    orderId: Optional[Any] = None
    rating: Optional[Any] = None
    userId: Optional[Any] = None

class PromoStripsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    isActive: Optional[Any] = None
    text: Optional[Any] = None

class PromoStripsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    isActive: Optional[Any] = None
    text: Optional[Any] = None

class PushNotificationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    createdBy: Optional[Any] = None
    deliveredCount: Optional[Any] = None
    image: Optional[Any] = None
    link: Optional[Any] = None
    message: Optional[Any] = None
    readCount: Optional[Any] = None
    scheduledFor: Optional[Any] = None
    status: Optional[Any] = None
    title: Optional[Any] = None
    userBehavior: Optional[Any] = None
    userSegment: Optional[Any] = None

class PushNotificationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    createdBy: Optional[Any] = None
    deliveredCount: Optional[Any] = None
    image: Optional[Any] = None
    link: Optional[Any] = None
    message: Optional[Any] = None
    readCount: Optional[Any] = None
    scheduledFor: Optional[Any] = None
    status: Optional[Any] = None
    title: Optional[Any] = None
    userBehavior: Optional[Any] = None
    userSegment: Optional[Any] = None

class CoachMarksInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    anchorId: Optional[Any] = None
    description: Optional[Any] = None
    isActive: Optional[Any] = None
    screenName: Optional[Any] = None
    sequenceOrder: Optional[Any] = None
    title: Optional[Any] = None

class CoachMarksInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    anchorId: Optional[Any] = None
    description: Optional[Any] = None
    isActive: Optional[Any] = None
    screenName: Optional[Any] = None
    sequenceOrder: Optional[Any] = None
    title: Optional[Any] = None

class CategoryTagsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    description: Optional[Any] = None
    isActive: Optional[Any] = None
    name: Optional[Any] = None

class CategoryTagsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    description: Optional[Any] = None
    isActive: Optional[Any] = None
    name: Optional[Any] = None

class Google_reviewsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    lastUpdated: Optional[Any] = None
    method: Optional[Any] = None
    rating: Optional[Any] = None
    reviewCount: Optional[Any] = None

class Google_reviewsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    lastUpdated: Optional[Any] = None
    method: Optional[Any] = None
    rating: Optional[Any] = None
    reviewCount: Optional[Any] = None

class StockReservationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    expiresAt: Optional[Any] = None
    productId: Optional[Any] = None
    quantity: Optional[Any] = None
    status: Optional[Any] = None
    userId: Optional[Any] = None

class StockReservationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    expiresAt: Optional[Any] = None
    productId: Optional[Any] = None
    quantity: Optional[Any] = None
    status: Optional[Any] = None
    userId: Optional[Any] = None

class ProductNotificationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    email: Optional[Any] = None
    phone: Optional[Any] = None
    productId: Optional[Any] = None
    status: Optional[Any] = None
    userId: Optional[Any] = None

class ProductNotificationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    email: Optional[Any] = None
    phone: Optional[Any] = None
    productId: Optional[Any] = None
    status: Optional[Any] = None
    userId: Optional[Any] = None

class ProductReviewsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    productId: Optional[Any] = None
    rating: Optional[Any] = None
    reviewText: Optional[Any] = None
    status: Optional[Any] = None
    userId: Optional[Any] = None

class ProductReviewsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    productId: Optional[Any] = None
    rating: Optional[Any] = None
    reviewText: Optional[Any] = None
    status: Optional[Any] = None
    userId: Optional[Any] = None

class ClassificationTagsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    isActive: Optional[Any] = None
    name: Optional[Any] = None

class ClassificationTagsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    isActive: Optional[Any] = None
    name: Optional[Any] = None

class ReviewClassificationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    category: Optional[Any] = None
    confidenceScore: Optional[Any] = None
    reviewId: Optional[Any] = None
    sentiment: Optional[Any] = None

class ReviewClassificationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    category: Optional[Any] = None
    confidenceScore: Optional[Any] = None
    reviewId: Optional[Any] = None
    sentiment: Optional[Any] = None

class AboutUsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    content: Optional[Any] = None
    isPublished: Optional[Any] = None
    title: Optional[Any] = None
    version: Optional[Any] = None

class AboutUsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    content: Optional[Any] = None
    isPublished: Optional[Any] = None
    title: Optional[Any] = None
    version: Optional[Any] = None

class PrivacyPolicyInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    content: Optional[Any] = None
    effectiveDate: Optional[Any] = None
    isActive: Optional[Any] = None
    version: Optional[Any] = None

class PrivacyPolicyInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    content: Optional[Any] = None
    effectiveDate: Optional[Any] = None
    isActive: Optional[Any] = None
    version: Optional[Any] = None

class AvailabilityRequestsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    pincode: Optional[Any] = None
    productId: Optional[Any] = None
    productName: Optional[Any] = None
    userEmail: Optional[Any] = None
    userName: Optional[Any] = None

class AvailabilityRequestsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    pincode: Optional[Any] = None
    productId: Optional[Any] = None
    productName: Optional[Any] = None
    userEmail: Optional[Any] = None
    userName: Optional[Any] = None

class PincodeSearchesInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    isServiceable: Optional[Any] = None
    pincode: Optional[Any] = None
    query: Optional[Any] = None
    timestamp: Optional[Any] = None

class PincodeSearchesInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    isServiceable: Optional[Any] = None
    pincode: Optional[Any] = None
    query: Optional[Any] = None
    timestamp: Optional[Any] = None

class SystemSettingsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    allowSignups: Optional[Any] = None
    defaultCurrency: Optional[Any] = None
    maintenanceMode: Optional[Any] = None
    maxUploadSizeMb: Optional[Any] = None
    timezone: Optional[Any] = None

class SystemSettingsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    allowSignups: Optional[Any] = None
    defaultCurrency: Optional[Any] = None
    maintenanceMode: Optional[Any] = None
    maxUploadSizeMb: Optional[Any] = None
    timezone: Optional[Any] = None

class ValetPayoutSettingsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    deliveryChargePerOrder: Optional[Any] = None
    returnPickupChargePerOrder: Optional[Any] = None

class ValetPayoutSettingsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    deliveryChargePerOrder: Optional[Any] = None
    returnPickupChargePerOrder: Optional[Any] = None

