"""
Router for Visual Search and Image Text Extraction.
Allows users to snap photos of products, covers, or handwritten lists
and receive matching search keywords and products.
"""

from typing import Optional, List
import base64
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Query
from pydantic import BaseModel

from app.services.visual_search_service import visual_search_service
from app.repositories.product_repository import product_repository
from app.models.product import ProductFilter
from app.utils.logger import logger

router = APIRouter()


class VisualSearchResponse(BaseModel):
    searchQuery: str
    extractedText: Optional[str] = ""
    brand: Optional[str] = None
    category: Optional[str] = None
    confidence: float = 0.0
    engineUsed: str = "unknown"
    products: Optional[List[dict]] = []


@router.post("/scan", response_model=VisualSearchResponse)
async def scan_product_image(
    file: Optional[UploadFile] = File(None),
    imageBase64: Optional[str] = Form(None),
    limit: int = Query(8, ge=1, le=20),
):
    """Scan an image file or base64 data to extract product search keywords.
    Free engines (Gemini Free Tier & Local OCR) are used by default.
    Paid engines (Google Cloud Vision, OpenAI GPT-4o, AWS Rekognition) are commented out in visual_search_service.py.
    """
    image_bytes: Optional[bytes] = None

    if file:
        image_bytes = await file.read()
    elif imageBase64:
        try:
            # Handle potential data URL prefix
            if "," in imageBase64:
                _, imageBase64 = imageBase64.split(",", 1)
            image_bytes = base64.b64decode(imageBase64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")

    if not image_bytes:
        raise HTTPException(status_code=400, detail="No image provided. Please upload a file or base64 string.")

    try:
        result = await visual_search_service.scan_image(image_bytes)
        
        products_list = []
        if result.search_query.strip():
            # Query the catalog to find immediate matches
            query_filter = ProductFilter(
                search=result.search_query.strip(),
                brand=result.brand,
                role="customer",
            )
            matched_products, _, _, _, _ = await product_repository.get_catalog(
                query_filter, skip=0, limit=limit
            )
            for p in matched_products:
                products_list.append({
                    "id": p.id,
                    "productId": p.productId,
                    "name": p.name,
                    "productName": p.name,
                    "brand": p.brand,
                    "category": p.category,
                    "price": p.price,
                    "displayImage": p.displayImage or (p.images[0] if p.images else None),
                })

        return VisualSearchResponse(
            searchQuery=result.search_query,
            extractedText=result.extracted_text,
            brand=result.brand,
            category=result.category,
            confidence=result.confidence,
            engineUsed=result.engine_used,
            products=products_list,
        )
    except Exception as e:
        logger.error(f"[VisualSearch] Error processing image scan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Visual search failed: {str(e)}")
