from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import MessageResponse
import asyncio
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.repositories.content_repository import about_repository, faq_repository, privacy_repository
from app.utils.auth import require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


# ── FAQ Models ──────────────────────────────────────────────────────────


class FAQItem(BaseModel):
    question: str
    answer: str


class FAQSectionCreate(BaseModel):
    title: str = Field(..., min_length=1)
    icon: Optional[str] = "help-circle-outline"
    displayOrder: Optional[int] = 0
    items: List[FAQItem] = []


class FAQSectionUpdate(BaseModel):
    title: Optional[str] = None
    icon: Optional[str] = None
    displayOrder: Optional[int] = None
    items: Optional[List[FAQItem]] = None


# ── Content Page Models ─────────────────────────────────────────────────


class ContentSection(BaseModel):
    title: str
    body: str


class AboutUsUpdate(BaseModel):
    brandName: Optional[str] = None
    tagline: Optional[str] = None
    mission: Optional[str] = None
    offerings: Optional[List[str]] = None
    contactEmail: Optional[str] = None
    contactWebsite: Optional[str] = None
    sections: Optional[List[ContentSection]] = None



class FAQSectionResponse(BaseModel):
    id: str = Field(alias="_id")
    title: str
    order: int
    isActive: bool
    questions: List[Dict[str, Any]]
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class AboutUsResponse(BaseModel):
    id: str = Field(alias="_id")
    title: str
    content: str
    imageUrls: List[str]
    isActive: bool
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

class PrivacyPolicyResponse(BaseModel):
    id: str = Field(alias="_id")
    title: str
    content: str
    version: str
    isActive: bool
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    publishedAt: Optional[str] = None

class PrivacyPolicyUpdate(BaseModel):
    lastUpdated: Optional[str] = None
    sections: Optional[List[ContentSection]] = None
    version: Optional[str] = None  # e.g. "1.0", "1.0.1", "2.0" — kept unchanged if omitted


# ═══════════════════════════════════════════════════════════════════════
# FAQ Endpoints
# ═══════════════════════════════════════════════════════════════════════


@router.get("/faq/public", response_model=List[FAQSectionResponse])
@cache.ttl_cache(ttl=3600.0)
async def get_public_faq():
    return await faq_repository.find_all()


@router.get("/faq", response_model=List[FAQSectionResponse])
async def get_all_faq(user: User = Depends(require_super_admin)):
    return await faq_repository.find_all()


@router.post("/faq", response_model=FAQSectionResponse)
async def create_faq_section(data: FAQSectionCreate, user: User = Depends(require_super_admin)):
    return await faq_repository.create_section(data)


@router.put("/faq/{section_id}", response_model=FAQSectionResponse)
async def update_faq_section(section_id: str, data: FAQSectionUpdate, user: User = Depends(require_super_admin)):
    existing = await faq_repository.find_by_id(section_id)
    if not existing:
        raise HTTPException(status_code=404, detail="FAQ section not found")
    return await faq_repository.update_section(section_id, data)


@router.delete("/faq/{section_id}", response_model=MessageResponse)
async def delete_faq_section(section_id: str, user: User = Depends(require_super_admin)):
    existing = await faq_repository.find_by_id(section_id)
    if not existing:
        raise HTTPException(status_code=404, detail="FAQ section not found")
    return await faq_repository.delete_section(section_id)


# ═══════════════════════════════════════════════════════════════════════
# About Us Endpoints
# ═══════════════════════════════════════════════════════════════════════


@router.get("/about/public", response_model=AboutUsResponse)
@cache.ttl_cache(ttl=3600.0)
async def get_public_about():
    doc = await about_repository.get()
    return doc or {}


@router.get("/about", response_model=AboutUsResponse)
async def get_about(user: User = Depends(require_super_admin)):
    doc = await about_repository.get()
    return doc or {}


@router.put("/about", response_model=AboutUsResponse)
async def update_about(data: AboutUsUpdate, user: User = Depends(require_super_admin)):
    return await about_repository.upsert(data)


# ═══════════════════════════════════════════════════════════════════════
# Privacy Policy Endpoints
# ═══════════════════════════════════════════════════════════════════════


@router.get("/privacy/public", response_model=PrivacyPolicyResponse)
@cache.ttl_cache(ttl=3600.0)
async def get_public_privacy():
    doc = await privacy_repository.get()
    return doc or {}


@router.get("/privacy", response_model=PrivacyPolicyResponse)
async def get_privacy(user: User = Depends(require_super_admin)):
    doc = await privacy_repository.get()
    return doc or {}


@router.put("/privacy", response_model=PrivacyPolicyResponse)
async def update_privacy(data: PrivacyPolicyUpdate, user: User = Depends(require_super_admin)):
    result = await privacy_repository.upsert(data)

    # Fire-and-forget background task to email all users
    last_updated = data.lastUpdated or result.last_updated
    version = result.version or "1"
    asyncio.create_task(_notify_all_users_of_privacy_update(last_updated, str(version)))

    return result


@router.get("/privacy/history", response_model=List[PrivacyPolicyResponse])
async def get_privacy_version_history(user: User = Depends(require_super_admin)):
    """Return the full version history of the Privacy Policy."""
    doc = await privacy_repository.get()
    if not doc:
        return {"version": 0, "versionHistory": []}
    return {
        "version": (doc.version if doc.version is not None else 1),
        "versionHistory": (doc.version_history or []),
    }


async def _notify_all_users_of_privacy_update(last_updated: str, version: str) -> None:
    """Background task: email all users (including admins) about the updated Privacy Policy."""
    try:
        from app.repositories.user_repository import user_repository
        from app.services.email_service import email_service

        frontend_url = os.getenv("FRONTEND_URL", "https://stationeryjunction.in")
        policy_url = f"{frontend_url.rstrip('/')}/privacy-policy"

        all_users = await user_repository.findAll()

        # Notify every user that has an email address
        recipients = [u for u in all_users if u.email]

        logger.info(
            "Privacy policy v%d updated — notifying %d user(s) via email",
            version,
            len(recipients),
        )

        sent = 0
        failed = 0
        batch_size = 20

        for i in range(0, len(recipients), batch_size):
            batch = recipients[i : i + batch_size]
            for user in batch:
                try:
                    ok = email_service.send_privacy_policy_update_email(
                        to_email=user.email,
                        last_updated=last_updated,
                        version=version,
                        policy_url=policy_url,
                    )
                    if ok:
                        sent += 1
                    else:
                        failed += 1
                except Exception as exc:
                    failed += 1
                    logger.error(
                        "Failed to send privacy policy email to %s: %s",
                        user.email,
                        exc,
                    )

            # Brief pause between batches to avoid SMTP rate limits
            if i + batch_size < len(recipients):
                await asyncio.sleep(1)

        logger.info("Privacy policy notification complete — sent: %d, failed: %d", sent, failed)
    except Exception as exc:
        logger.error("Privacy policy notification task crashed: %s", exc, exc_info=True)
