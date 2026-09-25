import re

filepath = r"app\routers\tracking.py"
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the base class to CamelBaseModel
if "from app.models.base import CamelBaseModel" not in text:
    text = text.replace("from pydantic import BaseModel", "from pydantic import BaseModel\nfrom app.models.base import CamelBaseModel")

# Change all Request classes from BaseModel to CamelBaseModel
text = text.replace("class BaseTrackingRequest(BaseModel):", "class BaseTrackingRequest(CamelBaseModel):")
text = text.replace("class TrackSearchRequest(BaseTrackingRequest):", "class TrackSearchRequest(BaseTrackingRequest):") # unchanged, inherits
text = text.replace("class TrackViewRequest(BaseTrackingRequest):", "class TrackViewRequest(BaseTrackingRequest):")
text = text.replace("class TrackClickRequest(BaseTrackingRequest):", "class TrackClickRequest(BaseTrackingRequest):")
text = text.replace("class TrackAddToCartRequest(BaseTrackingRequest):", "class TrackAddToCartRequest(BaseTrackingRequest):")
text = text.replace("class SyncMobileAnalyticsRequest(BaseModel):", "class SyncMobileAnalyticsRequest(CamelBaseModel):")

# Fix fields in tracking.py
replacements = {
    "userId": "user_id",
    "sessionId": "session_id",
    "searchTerm": "search_term",
    "resultsCount": "results_count",
    "productIds": "product_ids",
    "productId": "product_id",
    "productName": "product_name",
    "filterType": "filter_type",
    "filterValue": "filter_value",
    "cartValue": "cart_value",
    "cartItems": "cart_items",
}
for camel, snake in replacements.items():
    text = re.sub(rf"\b{camel}\b", snake, text)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
