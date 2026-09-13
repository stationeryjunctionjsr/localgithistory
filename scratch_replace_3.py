import re

def replace_in_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(filepath, 'w') as f:
        f.write(content)

google_models = """
class GoogleReviewResponse(BaseModel):
    rating: float = 0.0
    reviewCount: str = "0"
    lastUpdated: str = ""
    method: Optional[str] = None
"""

recommendation_models = """
class SlotMetrics(BaseModel):
    section_view: int = 0
    product_view: int = 0
    add_to_cart: int = 0

class RecommendationMetricsResponse(BaseModel):
    days: int
    section_views: int
    product_views: int
    add_to_carts: int
    by_slot: Dict[str, SlotMetrics] = {}

class EventTrackResponse(BaseModel):
    ok: bool = True
"""

replace_in_file("backend/app/routers/google_reviews.py", {
    "from fastapi import APIRouter, HTTPException": "from fastapi import APIRouter, HTTPException\nfrom pydantic import BaseModel\n" + google_models,
    "@router.get(\"/rating\", response_model=Dict[str, Any])": "@router.get(\"/rating\", response_model=GoogleReviewResponse)",
    "@router.post(\"/refresh\", response_model=Dict[str, Any])": "@router.post(\"/refresh\", response_model=GoogleReviewResponse)"
})

replace_in_file("backend/app/routers/push_notifications.py", {
    "@router.post(\"/register-device\", response_model=Dict[str, Any])": "@router.post(\"/register-device\", response_model=MessageResponse)",
    "@router.post(\"/{notification_id}/mark-read\", response_model=Dict[str, Any])": "@router.post(\"/{notification_id}/mark-read\", response_model=MessageResponse)"
})

replace_in_file("backend/app/routers/recommendations.py", {
    "from pydantic import BaseModel": "from pydantic import BaseModel\n" + recommendation_models,
    "@router.get(\"/metrics\", response_model=Dict[str, Any])": "@router.get(\"/metrics\", response_model=RecommendationMetricsResponse)",
    "@router.post(\"/events\", response_model=Dict[str, Any])": "@router.post(\"/events\", response_model=EventTrackResponse)"
})

replace_in_file("backend/app/routers/wishlist.py", {
    "@router.post(\"\", response_model=Dict[str, Any])": "@router.post(\"\", response_model=MessageResponse)",
    "@router.post(\"/\", response_model=Dict[str, Any])": "@router.post(\"/\", response_model=MessageResponse)"
})

print("Done part 3")
