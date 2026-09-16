from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any, Dict

class UserOrderStatsResponse(BaseModel):
    userId: str
    name: str
    email: str
    totalOrders: int
    averageOrderValue: float
    daysSinceLastOrder: Optional[int] = None
    avgOrdersPerMonth: float

class ItemsByUserTypeResponse(BaseModel):
    role: str
    views: int
    searches: int

class ReturnsReportResponse(BaseModel):
    returnId: str
    orderId: str
    createdAt: str
    status: str
    refundValue: float
    userName: str
    userEmail: str
    itemCount: int
    paymentMethod: Optional[str] = None
    orderTotal: Optional[float] = None

class PaymentMethodsReportResponse(BaseModel):
    paymentMethod: str
    orderCount: int
    revenue: float
    avgOrderValue: float

class RevenueByCategoryResponse(BaseModel):
    category: str
    orderCount: int
    quantity: int
    revenue: float

class InventoryAlertResponse(BaseModel):
    productId: str
    name: str
    sku: Optional[str] = None
    category: str
    stock: int
    status: str

class FulfillmentTimeReportResponse(BaseModel):
    orderId: str
    orderNumber: str
    createdAt: str
    status: str
    orderTotal: float
    userName: str
    fulfillmentHours: Optional[float] = None
    fulfillmentDays: Optional[float] = None

class CouponUsageReportResponse(BaseModel):
    couponCode: str
    discountType: str
    discountValue: float
    usageCount: int
    totalDiscountGiven: float
    totalRevenue: float

class SalesByLocationReportResponse(BaseModel):
    location: str
    orderCount: int
    quantity: int
    revenue: float

class NewVsReturningCustomerSalesResponse(BaseModel):
    customerType: str
    orderCount: int
    revenue: float

class ItemsBoughtTogetherResponse(BaseModel):
    productAId: str
    productAName: str
    productBId: str
    productBName: str
    frequency: int

class SalesByDeviceReportResponse(BaseModel):
    deviceType: str
    orderCount: int
    revenue: float

class TopReturnedProductsResponse(BaseModel):
    productId: str
    productName: str
    category: str
    returnCount: int
    quantityReturned: int
    revenueLost: float

class InventoryValueByCategoryResponse(BaseModel):
    category: str
    productCount: int
    totalStock: int
    inventoryValue: float

class SessionsOverTimeResponse(BaseModel):
    period: str
    sessions: int
    visitors: int
    uniqueVisitors: int

class VisitorsNowResponse(BaseModel):
    windowMinutes: int
    activeVisitors: int
    loggedInSessions: int
    guestSessions: int

class SearchesNoClicksResponse(BaseModel):
    term: str
    searchCount: int
    totalResults: int
    avgResults: float

class SearchConversionResponse(BaseModel):
    totalSearchSessions: int
    convertedSessions: int
    nonConvertedSessions: int
    conversionRate: float

class BounceRateResponse(BaseModel):
    period: str
    totalSessions: int
    bouncedSessions: int
    bounceRate: float

class RFMSegmentsResponse(BaseModel):
    userId: str
    name: str
    email: str
    segment: str
    orderCount: int
    totalSpend: float
    recencyDays: Optional[int] = None
    lastOrder: Optional[str] = None

class CustomerFrequencyResponse(BaseModel):
    type: str
    customers: int
    customerPct: float
    orders: int
    avgOrders: float
    revenue: float

class NetSalesResponse(BaseModel):
    orderId: str
    orderNumber: str
    createdAt: str
    customerName: str
    status: str
    grossSales: float
    discount: float
    tax: float
    shipping: float
    netSales: float

class SalesHeatmapResponse(BaseModel):
    dayOfWeek: str
    hour: int
    orderCount: int
    revenue: float

class InventoryRunwayResponse(BaseModel):
    productId: str
    name: str
    category: str
    currentStock: int
    unitsSold30d: int
    avgDailySales: float
    daysRemaining: Optional[float] = None

class DiscountsAuditResponse(BaseModel):
    orderId: str
    orderNumber: str
    createdAt: str
    customerName: str
    grossSales: float
    discountApplied: float
    discountPct: float
    couponCode: Optional[str] = None
    discountType: Optional[str] = None
    discountValue: Optional[float] = None
    netAfterDiscount: float

class ProductsPctSoldResponse(BaseModel):
    productId: str
    name: str
    sku: Optional[str] = None
    category: str
    openingStock: int
    currentStock: int
    unitsSold: int
    pctSold: float

class BundlePerformanceReportResponse(BaseModel):
    bundleId: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    isActive: Optional[bool] = None
    price: Optional[float] = None
    orderCount: Optional[int] = None
    revenue: Optional[float] = None
    copiesSold: Optional[int] = None
    monthlyRevenue: Optional[List[Dict[str, Any]]] = None

class SalesByChannelDetailedResponse(BaseModel):
    channel: str
    channelLabel: str
    orderCount: int
    revenue: float
    revenuePct: float
    aov: float

class AllReportsSummaryResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
