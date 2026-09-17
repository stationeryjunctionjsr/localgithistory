from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Dict, List
from datetime import datetime

class ReturnSettingsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    returnDays: Optional[int] = None

class ReturnSettingsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    returnDays: Optional[int] = None

class OrderFeedbackInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    comment: Optional[str] = None
    deliveryComment: Optional[str] = None
    deliveryRating: Optional[int] = None
    feedbackType: Optional[str] = None
    orderId: Optional[str] = None
    rating: Optional[int] = None
    userId: Optional[str] = None

class OrderFeedbackInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    comment: Optional[str] = None
    deliveryComment: Optional[str] = None
    deliveryRating: Optional[int] = None
    feedbackType: Optional[str] = None
    orderId: Optional[str] = None
    rating: Optional[int] = None
    userId: Optional[str] = None

class PromoStripsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    isActive: Optional[bool] = None
    text: Optional[str] = None

class PromoStripsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    isActive: Optional[bool] = None
    text: Optional[str] = None

class PushNotificationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    createdBy: Optional[str] = None
    deliveredCount: Optional[int] = None
    image: Optional[str] = None
    link: Optional[str] = None
    message: Optional[str] = None
    readCount: Optional[int] = None
    scheduledFor: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None
    userBehavior: Optional[str] = None
    userSegment: Optional[str] = None

class PushNotificationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    createdBy: Optional[str] = None
    deliveredCount: Optional[int] = None
    image: Optional[str] = None
    link: Optional[str] = None
    message: Optional[str] = None
    readCount: Optional[int] = None
    scheduledFor: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None
    userBehavior: Optional[str] = None
    userSegment: Optional[str] = None

class CoachMarksInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    anchorId: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None
    screenName: Optional[str] = None
    sequenceOrder: Optional[int] = None
    title: Optional[str] = None

class CoachMarksInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    anchorId: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None
    screenName: Optional[str] = None
    sequenceOrder: Optional[int] = None
    title: Optional[str] = None

class CategoryTagsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    description: Optional[str] = None
    isActive: Optional[bool] = None
    name: Optional[str] = None

class CategoryTagsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    description: Optional[str] = None
    isActive: Optional[bool] = None
    name: Optional[str] = None

class Google_reviewsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    lastUpdated: Optional[str] = None
    method: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[int] = None

class Google_reviewsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    lastUpdated: Optional[str] = None
    method: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[int] = None

class StockReservationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expiresAt: Optional[str] = None
    productId: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    userId: Optional[str] = None

class StockReservationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expiresAt: Optional[str] = None
    productId: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    userId: Optional[str] = None

class ProductNotificationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: Optional[str] = None
    phone: Optional[str] = None
    productId: Optional[str] = None
    status: Optional[str] = None
    userId: Optional[str] = None

class ProductNotificationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: Optional[str] = None
    phone: Optional[str] = None
    productId: Optional[str] = None
    status: Optional[str] = None
    userId: Optional[str] = None

class ProductReviewsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    productId: Optional[str] = None
    rating: Optional[int] = None
    reviewText: Optional[str] = None
    status: Optional[str] = None
    userId: Optional[str] = None

class ProductReviewsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    productId: Optional[str] = None
    rating: Optional[int] = None
    reviewText: Optional[str] = None
    status: Optional[str] = None
    userId: Optional[str] = None

class ClassificationTagsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    isActive: Optional[bool] = None
    name: Optional[str] = None

class ClassificationTagsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    isActive: Optional[bool] = None
    name: Optional[str] = None

class ReviewClassificationsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: Optional[str] = None
    confidenceScore: Optional[float] = None
    reviewId: Optional[str] = None
    sentiment: Optional[str] = None

class ReviewClassificationsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: Optional[str] = None
    confidenceScore: Optional[float] = None
    reviewId: Optional[str] = None
    sentiment: Optional[str] = None

class AboutUsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: Optional[str] = None
    isPublished: Optional[bool] = None
    title: Optional[str] = None
    version: Optional[str] = None

class AboutUsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: Optional[str] = None
    isPublished: Optional[bool] = None
    title: Optional[str] = None
    version: Optional[str] = None

class PrivacyPolicyInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: Optional[str] = None
    effectiveDate: Optional[str] = None
    isActive: Optional[bool] = None
    version: Optional[str] = None

class PrivacyPolicyInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content: Optional[str] = None
    effectiveDate: Optional[str] = None
    isActive: Optional[bool] = None
    version: Optional[str] = None

class AvailabilityRequestsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    pincode: Optional[str] = None
    productId: Optional[str] = None
    productName: Optional[str] = None
    userEmail: Optional[str] = None
    userName: Optional[str] = None

class AvailabilityRequestsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    pincode: Optional[str] = None
    productId: Optional[str] = None
    productName: Optional[str] = None
    userEmail: Optional[str] = None
    userName: Optional[str] = None

class PincodeSearchesInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    isServiceable: Optional[bool] = None
    pincode: Optional[str] = None
    query: Optional[str] = None
    timestamp: Optional[str] = None

class PincodeSearchesInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    isServiceable: Optional[bool] = None
    pincode: Optional[str] = None
    query: Optional[str] = None
    timestamp: Optional[str] = None

class SystemSettingsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    allowSignups: Optional[bool] = None
    defaultCurrency: Optional[str] = None
    maintenanceMode: Optional[bool] = None
    maxUploadSizeMb: Optional[int] = None
    timezone: Optional[str] = None

class SystemSettingsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    allowSignups: Optional[bool] = None
    defaultCurrency: Optional[str] = None
    maintenanceMode: Optional[bool] = None
    maxUploadSizeMb: Optional[int] = None
    timezone: Optional[str] = None

class ValetPayoutSettingsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    deliveryChargePerOrder: Optional[float] = None
    returnPickupChargePerOrder: Optional[float] = None

class ValetPayoutSettingsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    deliveryChargePerOrder: Optional[float] = None
    returnPickupChargePerOrder: Optional[float] = None

class SupportTicketInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ticketNumber: str
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
    attachments: Optional[List[str]] = []
    assignedTo: Optional[str] = None
    responses: Optional[List['TicketResponseItem']] = []
    resolvedAt: Optional[str] = None
    closedAt: Optional[str] = None
    createdAt: Optional[str] = None

class SupportTicketInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Optional[str] = None
    resolvedAt: Optional[str] = None
    closedAt: Optional[str] = None
    responses: Optional[List['TicketResponseItem']] = None

from app.models.schemas import TicketResponseItem
