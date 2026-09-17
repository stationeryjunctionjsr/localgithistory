from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Dict, List
from datetime import datetime

class ReturnSettingsInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    returnDays: Optional[int] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class ReturnSettingsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    returnDays: Optional[int] = None

class ReturnSettingsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    returnDays: Optional[int] = None

class SchemeInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    description: Optional[str] = None
    discountType: Optional[str] = None
    discountValue: Optional[float] = None
    minOrderValue: Optional[float] = None
    validFrom: Optional[str] = None
    validUntil: Optional[str] = None
    isActive: Optional[bool] = None
    code: Optional[str] = None
    applicableRoles: Optional[List[str]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class SchemeInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    description: Optional[str] = None
    discountType: Optional[str] = None
    discountValue: Optional[float] = None
    minOrderValue: Optional[float] = None
    validFrom: Optional[str] = None
    validUntil: Optional[str] = None
    isActive: Optional[bool] = None
    code: Optional[str] = None
    applicableRoles: Optional[List[str]] = None

class SchemeInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Optional[str] = None
    description: Optional[str] = None
    discountType: Optional[str] = None
    discountValue: Optional[float] = None
    minOrderValue: Optional[float] = None
    validFrom: Optional[str] = None
    validUntil: Optional[str] = None
    isActive: Optional[bool] = None
    code: Optional[str] = None
    applicableRoles: Optional[List[str]] = None

class ContactInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    email: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None
    displayOrder: Optional[int] = None
    addresses: Optional[List[str]] = None
    phoneNumbers: Optional[List[str]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class ContactInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None
    displayOrder: Optional[int] = None
    addresses: Optional[List[str]] = None
    phoneNumbers: Optional[List[str]] = None

class ContactInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None
    displayOrder: Optional[int] = None
    addresses: Optional[List[str]] = None
    phoneNumbers: Optional[List[str]] = None

class OrderFeedbackInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    comment: Optional[str] = None
    deliveryComment: Optional[str] = None
    deliveryRating: Optional[int] = None
    feedbackType: Optional[str] = None
    orderId: Optional[str] = None
    rating: Optional[int] = None
    userId: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

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

class PromoStripsInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    isActive: Optional[bool] = None
    text: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class DeviceKeyInternal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    key: str
    value: str

class DeviceSubscriptionInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    userId: Optional[str] = None
    endpoint: Optional[str] = None
    expoToken: Optional[str] = None
    keys: Optional[List[DeviceKeyInternal]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class DeviceSubscriptionInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    userId: Optional[str] = None
    endpoint: Optional[str] = None
    expoToken: Optional[str] = None
    keys: Optional[List[DeviceKeyInternal]] = None

class DeviceSubscriptionInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    userId: Optional[str] = None
    endpoint: Optional[str] = None
    expoToken: Optional[str] = None
    keys: Optional[List[DeviceKeyInternal]] = None

class CollectionInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    isActive: Optional[bool] = None
    displayOrder: Optional[int] = None
    visiblePages: Optional[List[str]] = None
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[str]] = None
    productIds: Optional[List[str]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class CollectionInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    name: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    isActive: Optional[bool] = None
    displayOrder: Optional[int] = None
    visiblePages: Optional[List[str]] = None
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[str]] = None
    productIds: Optional[List[str]] = None

class CollectionInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    name: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    isActive: Optional[bool] = None
    displayOrder: Optional[int] = None
    visiblePages: Optional[List[str]] = None
    userSegments: Optional[List[str]] = None
    visibilityRules: Optional[List[str]] = None
    productIds: Optional[List[str]] = None

class SearchTagInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    tagId: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    isActive: Optional[bool] = None
    categories: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    productIds: Optional[List[str]] = None
    excludedProductIds: Optional[List[str]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class SearchTagInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    tagId: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    isActive: Optional[bool] = None
    categories: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    productIds: Optional[List[str]] = None
    excludedProductIds: Optional[List[str]] = None

class SearchTagInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    tagId: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    isActive: Optional[bool] = None
    categories: Optional[List[str]] = None
    subCategories: Optional[List[str]] = None
    brands: Optional[List[str]] = None
    collections: Optional[List[str]] = None
    productIds: Optional[List[str]] = None
    excludedProductIds: Optional[List[str]] = None

class CoachMarkInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    anchorId: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    screenName: Optional[str] = None
    sequenceOrder: Optional[int] = None
    isActive: Optional[bool] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class CoachMarkInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    anchorId: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    screenName: Optional[str] = None
    sequenceOrder: Optional[int] = None
    isActive: Optional[bool] = None

class CoachMarkInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    anchorId: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    screenName: Optional[str] = None
    sequenceOrder: Optional[int] = None
    isActive: Optional[bool] = None

class CategoryTagInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    name: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class CategoryTagInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    name: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None

class CategoryTagInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    name: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None

class DeliveryChargeTierInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    min: Optional[float] = None
    max: Optional[float] = None
    charge: Optional[float] = None

class DeliveryChargeInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    locationId: Optional[int] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    applyDefaultCharge: Optional[bool] = None
    charge: Optional[float] = None
    minCartValue: Optional[float] = None
    serviceableForCustomer: Optional[bool] = None
    serviceableForRetailer: Optional[bool] = None
    serviceableForWholesaler: Optional[bool] = None
    isActive: Optional[bool] = None
    description: Optional[str] = None
    urgentDeliveryAvailable: Optional[bool] = None
    urgentDeliveryCharge: Optional[float] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class DeliveryChargeInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    locationId: Optional[int] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    applyDefaultCharge: Optional[bool] = None
    charge: Optional[float] = None
    minCartValue: Optional[float] = None
    serviceableForCustomer: Optional[bool] = None
    serviceableForRetailer: Optional[bool] = None
    serviceableForWholesaler: Optional[bool] = None
    isActive: Optional[bool] = None
    description: Optional[str] = None
    urgentDeliveryAvailable: Optional[bool] = None
    urgentDeliveryCharge: Optional[float] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliveryChargeInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    locationId: Optional[int] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    applyDefaultCharge: Optional[bool] = None
    charge: Optional[float] = None
    minCartValue: Optional[float] = None
    serviceableForCustomer: Optional[bool] = None
    serviceableForRetailer: Optional[bool] = None
    serviceableForWholesaler: Optional[bool] = None
    isActive: Optional[bool] = None
    description: Optional[str] = None
    urgentDeliveryAvailable: Optional[bool] = None
    urgentDeliveryCharge: Optional[float] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliveryChargeDefaultInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    applicableToWholesaler: Optional[bool] = None
    applicableToRetailer: Optional[bool] = None
    isActive: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class DeliveryChargeDefaultInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    applicableToWholesaler: Optional[bool] = None
    applicableToRetailer: Optional[bool] = None
    isActive: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class DeliveryChargeDefaultInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    applicableToWholesaler: Optional[bool] = None
    applicableToRetailer: Optional[bool] = None
    isActive: Optional[bool] = None
    tiers: Optional[List[DeliveryChargeTierInternal]] = None

class PromoStripsInternalCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    isActive: Optional[bool] = None
    text: Optional[str] = None

class PromoStripsInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    isActive: Optional[bool] = None
    text: Optional[str] = None

class PushNotificationsInternal(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    id: Optional[str] = Field(None, alias="_id")
    title: Optional[str] = None
    message: Optional[str] = None
    link: Optional[str] = None
    image: Optional[str] = None
    status: Optional[str] = None
    scheduledFor: Optional[str] = None
    deliveredCount: Optional[int] = None
    readCount: Optional[int] = None
    userSegment: Optional[str] = None
    userBehavior: Optional[str] = None
    createdBy: Optional[str] = None
    targetedUserIds: Optional[List[str]] = None
    readByUserIds: Optional[List[str]] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

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
    userSegment: Optional[str] = None
    userBehavior: Optional[str] = None

    userSegment: Optional[str] = None
    userBehavior: Optional[str] = None
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
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
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
    attachments: Optional[List[str]] = None
    assignedTo: Optional[str] = None
    responses: Optional[List[dict]] = None
    resolvedAt: Optional[str] = None
    closedAt: Optional[str] = None
    createdAt: Optional[str] = None

class SupportTicketInternalUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)
    assignedTo: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    resolvedAt: Optional[str] = None
    closedAt: Optional[str] = None
    responses: Optional[List[dict]] = None

from app.models.schemas import TicketResponseItem

class ActivityMetaInternal(BaseModel):
    key: str
    value: str

class ActivityInternalCreate(BaseModel):
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    action: str
    comment: Optional[str] = None
    isGuest: Optional[bool] = None
    userAgent: Optional[str] = None
    os: Optional[str] = None
    osVersion: Optional[str] = None
    deviceType: Optional[str] = None
    meta: Optional[List[ActivityMetaInternal]] = None

class ActivityInternalUpdate(BaseModel):
    userId: Optional[str] = None
    isGuest: Optional[bool] = None
    comment: Optional[str] = None

class ActivityInternal(BaseModel):
    id: str = Field(alias="_id")
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    action: str
    comment: Optional[str] = None
    isGuest: Optional[bool] = None
    userAgent: Optional[str] = None
    os: Optional[str] = None
    osVersion: Optional[str] = None
    deviceType: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    meta: Optional[List[ActivityMetaInternal]] = None

class ReturnRequestItemInternal(BaseModel):
    productId: str
    quantity: int
    reason: Optional[str] = None

class ReturnRequestValetDeclineInternal(BaseModel):
    valetId: str
    reason: Optional[str] = None

class ReturnRequestInternal(BaseModel):
    id: str = Field(alias="_id")
    returnId: Optional[str] = None
    orderId: Optional[str] = None
    userId: Optional[str] = None
    paymentMethod: Optional[str] = None
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    valetId: Optional[str] = None
    sellerId: Optional[str] = None
    deliverySlotId: Optional[str] = None
    deliverySlotConfigId: Optional[str] = None
    deliverySlotDate: Optional[str] = None
    pendingValetId: Optional[str] = None
    valetAssignedAt: Optional[str] = None
    valetCascadeCount: Optional[int] = None
    deliveryCharge: Optional[float] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    items: Optional[List[ReturnRequestItemInternal]] = None
    valetDeclineHistory: Optional[List[ReturnRequestValetDeclineInternal]] = None
    notes: Optional[str] = None

class ReturnRequestInternalCreate(BaseModel):
    returnId: Optional[str] = None
    orderId: Optional[str] = None
    userId: Optional[str] = None
    paymentMethod: Optional[str] = None
    upiPaymentScreenshot: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    valetId: Optional[str] = None
    sellerId: Optional[str] = None
    deliverySlotId: Optional[str] = None
    deliverySlotConfigId: Optional[str] = None
    deliverySlotDate: Optional[str] = None
    pendingValetId: Optional[str] = None
    valetAssignedAt: Optional[str] = None
    valetCascadeCount: Optional[int] = None
    deliveryCharge: Optional[float] = None
    items: Optional[List[ReturnRequestItemInternal]] = None
    valetDeclineHistory: Optional[List[ReturnRequestValetDeclineInternal]] = None
    notes: Optional[str] = None

class ReturnRequestInternalUpdate(BaseModel):
    status: Optional[str] = None
    valetId: Optional[str] = None
    pendingValetId: Optional[str] = None
    valetAssignedAt: Optional[str] = None
    valetCascadeCount: Optional[int] = None
    valetDeclineHistory: Optional[List[ReturnRequestValetDeclineInternal]] = None
    notes: Optional[str] = None
