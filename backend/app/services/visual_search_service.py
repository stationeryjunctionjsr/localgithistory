"""
Visual Search & Image OCR Service for Stationery Junction.

Supports extracting product names, brand labels, and clean search keywords
from packaging, notebook covers, stationery items, or handwritten shopping notes.

Engines:
1. Google Gemini 2.0 / 1.5 Flash Vision (FREE Tier: 1,500 requests/day via Google AI Studio) [ACTIVE]
2. Local Heuristic / OCR Fallback [ACTIVE]
3. Google Cloud Vision API [PAID - COMMENTED OUT]
4. OpenAI GPT-4o Vision API [PAID - COMMENTED OUT]
5. AWS Rekognition [PAID - COMMENTED OUT]
"""

import base64
import io
import json
import os
import re
from typing import Any, Dict, List, Optional
from PIL import Image
import httpx

from app.utils.logger import logger


class VisualSearchResult:
    def __init__(
        self,
        search_query: str,
        extracted_text: str = "",
        brand: Optional[str] = None,
        category: Optional[str] = None,
        confidence: float = 0.9,
        engine_used: str = "gemini_free",
    ):
        self.search_query = search_query
        self.extracted_text = extracted_text
        self.brand = brand
        self.category = category
        self.confidence = confidence
        self.engine_used = engine_used

    def to_dict(self) -> Dict[str, Any]:
        return {
            "searchQuery": self.search_query,
            "extractedText": self.extracted_text,
            "brand": self.brand,
            "category": self.category,
            "confidence": self.confidence,
            "engineUsed": self.engine_used,
        }


class VisualSearchService:
    def __init__(self):
        # Read API keys from environment
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        # Paid keys (commented out / disabled by default)
        # self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        # self.google_cloud_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        # self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", "")

    def _preprocess_image(self, image_bytes: bytes, max_dim: int = 1024) -> bytes:
        """Resize image if needed to optimize network transfer and speed up inference."""
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Convert RGBA/P to RGB if saving to JPEG
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Resize if larger than max_dim
                width, height = img.size
                if max(width, height) > max_dim:
                    if width > height:
                        new_w = max_dim
                        new_h = int(height * (max_dim / width))
                    else:
                        new_h = max_dim
                        new_w = int(width * (max_dim / height))
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                return buf.getvalue()
        except Exception as e:
            logger.warning(f"[VisualSearch] Image preprocessing failed, using raw bytes: {e}")
            return image_bytes

    async def scan_image(self, image_bytes: bytes) -> VisualSearchResult:
        """Main entry point: tries free AI vision (Gemini), falling back to local heuristic/OCR.
        Paid services are implemented and commented out below.
        """
        processed_bytes = self._preprocess_image(image_bytes)

        # -------------------------------------------------------------------------
        # [FREE ENGINE 1]: Google Gemini Flash Vision (1,500 free requests/day)
        # -------------------------------------------------------------------------
        if self.gemini_api_key:
            try:
                gemini_res = await self._scan_with_gemini(processed_bytes)
                if gemini_res and gemini_res.search_query.strip():
                    return gemini_res
            except Exception as e:
                logger.error(f"[VisualSearch] Gemini free tier call failed: {e}", exc_info=True)

        # -------------------------------------------------------------------------
        # [PAID ENGINE 3 - COMMENTED OUT]: Google Cloud Vision API
        # To enable:
        # 1. pip install google-cloud-vision
        # 2. Set GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json in .env
        # 3. Uncomment the block below
        # -------------------------------------------------------------------------
        # try:
        #     paid_gcv_result = await self._scan_with_google_cloud_vision(processed_bytes)
        #     if paid_gcv_result:
        #         return paid_gcv_result
        # except Exception as e:
        #     logger.error(f"[VisualSearch] Google Cloud Vision failed: {e}")

        # -------------------------------------------------------------------------
        # [PAID ENGINE 4 - COMMENTED OUT]: OpenAI GPT-4o Vision API
        # To enable:
        # 1. pip install openai
        # 2. Set OPENAI_API_KEY=sk-... in .env
        # 3. Uncomment the block below
        # -------------------------------------------------------------------------
        # try:
        #     paid_openai_result = await self._scan_with_openai_vision(processed_bytes)
        #     if paid_openai_result:
        #         return paid_openai_result
        # except Exception as e:
        #     logger.error(f"[VisualSearch] OpenAI GPT-4o Vision failed: {e}")

        # -------------------------------------------------------------------------
        # [PAID ENGINE 5 - COMMENTED OUT]: AWS Rekognition Text/Label Detection
        # To enable:
        # 1. pip install boto3
        # 2. Set AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY in .env
        # 3. Uncomment the block below
        # -------------------------------------------------------------------------
        # try:
        #     paid_aws_result = await self._scan_with_aws_rekognition(processed_bytes)
        #     if paid_aws_result:
        #         return paid_aws_result
        # except Exception as e:
        #     logger.error(f"[VisualSearch] AWS Rekognition failed: {e}")

        # -------------------------------------------------------------------------
        # [FREE ENGINE 2]: Fallback Heuristic / Local OCR
        # -------------------------------------------------------------------------
        return self._scan_with_local_fallback(processed_bytes)

    async def _scan_with_gemini(self, image_bytes: bytes) -> Optional[VisualSearchResult]:
        """Free Tier Gemini 2.0 / 1.5 Flash Vision via Google AI Studio REST API.
        Generous free quota: 15 requests per minute, 1,500 requests per day at $0 cost.
        """
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = (
            "You are a visual search assistant for Stationery Junction (an online stationery & office supplies store). "
            "Analyze the attached image (which could be a stationery product, book cover, pen, notebook, art material, "
            "packaging label, or handwritten shopping list). "
            "Extract:\n"
            "1. 'search_query': The cleanest, most relevant concise search keyword string to look up in our product catalog "
            "(e.g., 'Classmate 200 pages spiral notebook', 'Camlin Artists Acrylic Colour', 'Reynolds 045 Ball Pen'). "
            "EXCLUDE clutter like barcode numbers, MRP/pricing (e.g. 'Rs 50'), manufacturing dates, batch codes, or legal notices.\n"
            "2. 'extracted_text': The primary visible brand or product text found on the item.\n"
            "3. 'brand': Recognized brand name (e.g., Classmate, Doms, Camlin, Faber-Castell, Luxor, Casio, Apsara) if visible, or null.\n"
            "4. 'category': Broad stationery category (e.g., Notebooks, Pens, Art Supplies, Adhesives, Desk Organizers) if visible, or null.\n\n"
            "Output purely valid JSON in this format with no markdown wrappers:\n"
            "{\"search_query\": \"...\", \"extracted_text\": \"...\", \"brand\": \"...\", \"category\": \"...\"}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64_image,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.warning(f"[VisualSearch] Gemini API returned status {resp.status_code}: {resp.text}")
                return None
            
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return None
            
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return None
            
            raw_text = parts[0].get("text", "").strip()
            # Clean markdown if present
            raw_text = re.sub(r"^```json\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)
            
            parsed = json.loads(raw_text)
            search_query = parsed.get("search_query", "").strip()
            extracted_text = parsed.get("extracted_text", "").strip()
            brand = parsed.get("brand") or None
            category = parsed.get("category") or None

            return VisualSearchResult(
                search_query=search_query or extracted_text,
                extracted_text=extracted_text,
                brand=brand,
                category=category,
                confidence=0.95,
                engine_used="gemini_free_tier",
            )

    def _scan_with_local_fallback(self, image_bytes: bytes) -> VisualSearchResult:
        """Local heuristic / zero-cost fallback when no external API key is set."""
        # Simple fallback message prompting the user or extracting basic dimensions
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                w, h = img.size
                desc = f"Image ({w}x{h})"
        except Exception:
            desc = "Scanned Image"

        return VisualSearchResult(
            search_query="",
            extracted_text=f"Detected {desc}. Add GEMINI_API_KEY to .env for AI product extraction.",
            confidence=0.5,
            engine_used="local_fallback",
        )

    # =========================================================================
    # [PAID OPTIONS - COMMENTED OUT AS REQUESTED]
    # =========================================================================

    # async def _scan_with_google_cloud_vision(self, image_bytes: bytes) -> Optional[VisualSearchResult]:
    #     """[PAID] Google Cloud Vision API - Text & Label Detection.
    #     Cost: 1,000 requests/month free, then $1.50 per 1,000 requests.
    #     Setup:
    #       1. pip install google-cloud-vision
    #       2. Set GOOGLE_APPLICATION_CREDENTIALS in .env
    #     """
    #     from google.cloud import vision
    #     client = vision.ImageAnnotatorClient()
    #     image = vision.Image(content=image_bytes)
    #
    #     # Run text detection
    #     response = client.text_detection(image=image)
    #     texts = response.text_annotations
    #     if not texts:
    #         return None
    #
    #     full_text = texts[0].description
    #     # Filter out MRP, batch numbers, dates
    #     cleaned_query = re.sub(r"(MRP|RS|Rs|\.|\bPKG\b|\bBATCH\b|\bEXP\b|\bMFD\b|\d{2}/\d{4}|\d{10,})", " ", full_text, flags=re.IGNORECASE)
    #     cleaned_query = " ".join(cleaned_query.split()[:6])  # Take first 6 salient tokens
    #
    #     return VisualSearchResult(
    #         search_query=cleaned_query,
    #         extracted_text=full_text,
    #         confidence=0.92,
    #         engine_used="google_cloud_vision_paid",
    #     )

    # async def _scan_with_openai_vision(self, image_bytes: bytes) -> Optional[VisualSearchResult]:
    #     """[PAID] OpenAI GPT-4o / GPT-4o-mini Vision API.
    #     Cost: Pay per token (~$0.005 - $0.01 per image).
    #     Setup:
    #       1. pip install openai
    #       2. Set OPENAI_API_KEY=sk-... in .env
    #     """
    #     import openai
    #     client = openai.AsyncOpenAI(api_key=self.openai_api_key)
    #     b64 = base64.b64encode(image_bytes).decode("utf-8")
    #
    #     response = await client.chat.completions.create(
    #         model="gpt-4o-mini",
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": [
    #                     {"type": "text", "text": "Extract the stationery product name as concise search keywords JSON: {\"search_query\": \"...\"}"},
    #                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
    #                 ]
    #             }
    #         ],
    #         response_format={"type": "json_object"}
    #     )
    #     content = response.choices[0].message.content
    #     parsed = json.loads(content)
    #     return VisualSearchResult(
    #         search_query=parsed.get("search_query", ""),
    #         confidence=0.95,
    #         engine_used="openai_gpt4o_paid",
    #     )

    # async def _scan_with_aws_rekognition(self, image_bytes: bytes) -> Optional[VisualSearchResult]:
    #     """[PAID] AWS Rekognition Text & Object Detection.
    #     Cost: 1,000 transactions/month free for 12 months, then $1.00 per 1,000 images.
    #     Setup:
    #       1. pip install boto3
    #       2. Set AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY in .env
    #     """
    #     import boto3
    #     client = boto3.client("rekognition")
    #     response = client.detect_text(Image={"Bytes": image_bytes})
    #     detections = response.get("TextDetections", [])
    #     lines = [d["DetectedText"] for d in detections if d["Type"] == "LINE"]
    #     query = " ".join(lines[:4])
    #     return VisualSearchResult(
    #         search_query=query,
    #         extracted_text="\n".join(lines),
    #         confidence=0.88,
    #         engine_used="aws_rekognition_paid",
    #     )


visual_search_service = VisualSearchService()
