from typing import Dict, Any, List
from app.models.schemas import MessageResponse
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

class GoogleReviewResponse(BaseModel):
    rating: float = 0.0
    reviewCount: str = "0"
    lastUpdated: str = ""
    method: Optional[str] = None


from app.repositories.google_review_repository import google_review_repository
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


@router.get("/rating", response_model=GoogleReviewResponse)
@cache.ttl_cache(ttl=300.0)
async def get_google_rating():
    return await google_review_repository.get_latest_rating()


@router.post("/refresh", response_model=GoogleReviewResponse)
async def refresh_google_rating():
    try:
        result = await google_review_repository.fetch_and_update()
        # Bust the GET /rating cache so the next page load reads fresh DB data
        cache.invalidate(get_google_rating)
        return result
    except Exception as e:
        logger.error("refresh_google_rating failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=503, detail="Service unavailable")
