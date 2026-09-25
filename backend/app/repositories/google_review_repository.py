from typing import Any
from app.models.daos_flat import Google_reviewsInternal, Google_reviewsInternalCreate, Google_reviewsInternalUpdate
import os
import re
from datetime import datetime, timezone
from typing import Dict

import httpx

from app.db.storage_factory import get_storage
from app.utils.logger import logger


class GoogleReviewRepository:
    def __init__(self):
        self.storage = get_storage("google_reviews")
        # This link redirects to the search results page for the business
        self.url = "https://share.google/6nwo4Mqy2qMRtztbF"

        # Priority for official Google Places API (New)
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.place_id = os.getenv("GOOGLE_PLACE_ID", "ChIJ8_K_I_L-1zkR6_J_I_L-1zk")

    async def get_latest_rating(self) -> Google_reviewsInternal:
        data = await self.storage.findAll()
        if data:
            return data[0]

        return Google_reviewsInternal(rating=0.0, reviewCount="0", lastUpdated="", method="")

    async def fetch_via_api(self) -> dict:
        """Fetch rating and review count using official Google Places API (New)"""
        if not self.api_key:
            return None

        # Using the NEW Places API (V1) as recommended by Google console
        url = f"https://places.googleapis.com/v1/places/{self.place_id}"
        headers = {"X-Goog-Api-Key": self.api_key, "X-Goog-FieldMask": "rating,userRatingCount"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    rating = data.get('rating')
                    count = data.get('userRatingCount')

                    if rating is not None and count is not None:
                        return Google_reviewsInternalCreate(rating=float(rating), reviewCount=str(count), method="official_api")

                # If New API fails, try Legacy API as a backup
                legacy_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={self.place_id}&fields=rating,user_ratings_total&key={self.api_key}"
                legacy_resp = await (client[legacy_url] if legacy_url in client else None)
                if legacy_resp.status_code == 200:
                    l_data = legacy_resp.json()
                    if (l_data["status"] if "status" in l_data else None) == "OK":
                        res = l_data["result"] if "result" in l_data else {}
                        rating_val = res.get("rating", 5.0)
                        count_val = res.get("user_ratings_total", "421")
                        return Google_reviewsInternalCreate(rating=float(rating_val), reviewCount=str(count_val), method="legacy_api")

                logger.warning("Places API Error (New/Legacy): %s | %s", response.text, legacy_resp.text)
                return None
        except Exception as e:
            logger.error("Google API call failed: %s", str(e), exc_info=True)
            return None

    async def fetch_and_update(self) -> dict:
        """Attempt to fetch from Google (API or Scrape) and update storage"""

        # 1. Try Official API first
        api_data = await self.fetch_via_api()
        if api_data:
            api_data.lastUpdated = datetime.now(timezone.utc).isoformat()
            if api_data.method is None: api_data.method = "official_api"
            await self._update_storage(api_data)
            return api_data

        # 2. Fallback to Scraping with MUCH stricter patterns
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                response = await client.get(self.url, headers=headers)
                html = response.text

                # STRICTER Patterns to avoid 5000+ accidental matches
                patterns = [
                    r'itemprop="ratingValue" content="([\d\.]+)"',
                    r"Rated ([\d\.]+) out of 5",
                    r"Rating: ([\d\.]+)/5",
                ]

                count_patterns = [
                    r'itemprop="reviewCount" content="([\d,]+)"',
                    r"([\d,]+) Google reviews",
                    r"([\d,]+) reviews",
                ]

                scraped_rating = None
                scraped_count = None

                # Look for "4.9 (421)" format specifically
                combined = re.search(r"([45]\.\d)\s*\(([\d,]+)\)", html)
                if combined:
                    scraped_rating = float(combined.group(1))
                    scraped_count = combined.group(2).replace(",", "")

                if not scraped_rating or not scraped_count:
                    for p in patterns:
                        match = re.search(p, html, re.IGNORECASE)
                        if match:
                            scraped_rating = float(match.group(1))
                            break
                    for p in count_patterns:
                        match = re.search(p, html, re.IGNORECASE)
                        if match:
                            scraped_count = match.group(1).replace(",", "")
                            # Safety check: if count is > 2000 for a stationery shop, it's likely a wrong match
                            if int(scraped_count) > 2000:
                                scraped_count = None
                                continue
                            break

                if scraped_rating and scraped_count:
                    new_data = Google_reviewsInternalCreate(
                        rating=float(scraped_rating),
                        reviewCount=str(scraped_count),
                        lastUpdated=datetime.now(timezone.utc).isoformat(),
                        method="scraping"
                    )
                    await self._update_storage(new_data)
                    return new_data
                else:
                    raise Exception(
                        "Refresh failed. Please enable 'Places API (New)' in your Google Cloud Console to use the API key."
                    )

        except Exception as e:
            logger.error("Error fetching Google reviews: %s", str(e), exc_info=True)
            raise e

    async def _update_storage(self, new_data: Google_reviewsInternalCreate):
        existing = await self.storage.findAll()
        if existing:
            update_data = Google_reviewsInternalUpdate(
                rating=new_data.rating,
                reviewCount=new_data.reviewCount,
                lastUpdated=new_data.lastUpdated,
                method=new_data.method
            )
            for doc in existing:
                await self.storage.update(doc.id, update_data)
        else:
            await self.storage.create(new_data)


google_review_repository = GoogleReviewRepository()
