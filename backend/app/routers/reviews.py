from app.models.daos import ProductInternalUpdate
from app.models.user import User
from app.models.schemas import MessageResponse, ProductReviewResponse, ClassificationTagResponse, ReviewActionResponse, ClassificationActionResponse
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.repositories.order_repository import order_repository
from app.repositories.product_repository import product_repository
from app.repositories.product_review_repository import product_review_repository
from app.repositories.review_classification_repository import review_classification_repository
from app.utils.auth import get_current_user, require_super_admin
from app.utils.cache import cache
from app.utils.logger import logger

router = APIRouter()


# --- Customer Schemas ---
class ReviewCreate(BaseModel):
    productId: str
    rating: int = Field(..., ge=1, le=5)
    comment: str
    classification: str


# --- Admin Schemas ---
class ClassificationCreate(BaseModel):
    name: str


class ClassificationUpdate(BaseModel):
    name: Optional[str] = None
    isActive: Optional[bool] = None


# --- Customer Endpoints ---


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ReviewActionResponse)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ReviewActionResponse)
async def create_review(review_data: ReviewCreate, current_user: User = Depends(get_current_user)):
    """Submit a rating and review for a delivered product."""
    user_id = str(current_user.id)
    product_id = str(review_data.productId)

    # 1. Verify that the product exists
    product = await product_repository.findById(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # 2. Verify that the user has a delivered order with this product
    orders = await order_repository.findByUser(user_id, status="delivered")
    has_purchased = False
    for order in orders:
        items = (order.items or [])
        for item in items:
            if str(item.product_id or "") == product_id:
                has_purchased = True
                break
        if has_purchased:
            break

    if not has_purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only review products that have been successfully delivered to you.",
        )

    # 3. Verify that the classification is valid and active
    classifications = await review_classification_repository.find_active()
    valid_class = False
    for c in classifications:
        if (c.name or "").strip().lower() == review_data.classification.strip().lower():
            valid_class = True
            # Normalize key
            review_data.classification = c.name
            break

    if not valid_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid review classification: '{review_data.classification}'",
        )

    # 4. Create review with status 'pending'
    from app.models.daos_flat import ProductReviewsInternalCreate
    review = ProductReviewsInternalCreate(
        product_id=product_id,
        user_id=user_id,
        user_name=(current_user.name if current_user.name is not None else "Verified Buyer"),
        rating=review_data.rating,
        review_text=review_data.comment.strip(),
        classification=review_data.classification,
        status="pending",
    )

    created = await product_review_repository.create(review)
    return ReviewActionResponse(message="Review submitted successfully and is pending moderation.", review=created)


@router.get("/product/{product_id}", response_model=List[ProductReviewResponse])
@cache.ttl_cache(ttl=600.0)
async def get_product_reviews(product_id: str):
    """Retrieve all approved reviews for a product."""
    reviews = await product_review_repository.find_approved_by_product(product_id)

    # Sort reviews by creation date descending (newest first)
    reviews.sort(key=lambda r: (r.created_at or ""), reverse=True)
    return reviews


@router.get("/classifications", response_model=List[ClassificationTagResponse])
@cache.ttl_cache(ttl=3600.0)
async def get_active_classifications():
    """Retrieve all active review classifications."""
    return await review_classification_repository.find_active()


# --- Admin Endpoints ---


@router.get("/admin/list", response_model=List[ProductReviewResponse])
async def admin_get_all_reviews(status_filter: Optional[str] = None, current_user: User = Depends(require_super_admin)):
    """Get all reviews in the system, optionally filtered by status (super admin only)."""
    query = {}
    if status_filter:
        query["status"] = status_filter
    reviews = await product_review_repository.findAll(query)

    # Sort by creation date descending
    reviews.sort(key=lambda r: (r.created_at or ""), reverse=True)
    return reviews


@router.post("/admin/{review_id}/approve", response_model=ReviewActionResponse)
async def admin_approve_review(review_id: str, current_user: User = Depends(require_super_admin)):
    """Approve a product review to make it publicly visible (super admin only)."""
    review = await product_review_repository.findById(review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    updated = await product_review_repository.update(review_id, {"status": "approved"})

    # Recalculate average rating for the product
    try:
        product_id = review.product_id
        if product_id:
            all_approved = await product_review_repository.find_approved_by_product(product_id)
            if all_approved:
                avg_rating = sum(int((r.rating if r.rating is not None else 0)) for r in all_approved) / len(all_approved)
                await product_repository.update(
                    product_id, ProductInternalUpdate(rating=round(avg_rating, 2), reviews=len(all_approved))
                )
    except Exception as e:
        logger.error("Failed to update product aggregated rating after review approval (review %s): %s", review_id, str(e), exc_info=True)

    # Notify the reviewer — in-app notification + push
    try:
        from app.models.schemas import NotificationMetadata
        from app.utils.notify import notify_user
        reviewer_id = str(review.user_id) if review.user_id else None
        product_id_for_push = review.product_id
        if reviewer_id:
            product_obj = await product_repository.findById(product_id_for_push) if product_id_for_push else None
            product_name = (product_obj.name if product_obj else None) or "your product"
            await notify_user(
                user_id    = reviewer_id,
                notif_type = "review_approved",
                title      = "Your review is live! ⭐",
                message    = f"Your review for {product_name} has been approved and is now visible.",
                link       = f"/products/product/{product_id_for_push}" if product_id_for_push else "/",
                metadata   = NotificationMetadata(product_id=product_id_for_push),
            )
    except Exception as e:
        logger.warning("Notification failed for review approval %s: %s", review_id, str(e))

    return ReviewActionResponse(message="Review approved successfully", review=updated)


@router.post("/admin/{review_id}/remove", response_model=ReviewActionResponse)
async def admin_remove_review(review_id: str, current_user: User = Depends(require_super_admin)):
    """Reject/remove a review so it is hidden from the public (super admin only)."""
    review = await product_review_repository.findById(review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    from app.models.daos_flat import ProductReviewsInternalUpdate
    updated = await product_review_repository.update(review_id, ProductReviewsInternalUpdate(status="removed"))

    # Recalculate average rating for the product
    try:
        product_id = review.product_id
        if product_id:
            all_approved = await product_review_repository.find_approved_by_product(product_id)
            if all_approved:
                avg_rating = sum(int((r.rating if r.rating is not None else 0)) for r in all_approved) / len(all_approved)
                await product_repository.update(
                    product_id, ProductInternalUpdate(rating=round(avg_rating, 2), reviews=len(all_approved))
                )
            else:
                await product_repository.update(product_id, ProductInternalUpdate(rating=None, reviews=0))
    except Exception as e:
        logger.error("Failed to update product aggregated rating after review removal (review %s): %s", review_id, str(e), exc_info=True)

    return ReviewActionResponse(message="Review removed successfully", review=updated)


@router.get("/admin/classifications", response_model=List[ClassificationTagResponse])
async def admin_get_classifications(current_user: User = Depends(require_super_admin)):
    """Retrieve all review classifications (super admin only)."""
    return await review_classification_repository.findAll()


@router.post("/admin/classifications", response_model=ClassificationActionResponse)
async def admin_create_classification(
    class_data: ClassificationCreate, current_user: User = Depends(require_super_admin)
):
    """Create a new review classification (super admin only)."""
    name = class_data.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name cannot be empty")

    existing = await review_classification_repository.findAll()
    for c in existing:
        if (c.name or "").strip().lower() == name.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Classification already exists")

    from app.models.daos_flat import ClassificationTagsInternalCreate
    created = await review_classification_repository.create(ClassificationTagsInternalCreate(name=name, is_active=True))
    return ClassificationActionResponse(message="Classification created successfully", classification=created)


@router.put("/admin/classifications/{class_id}", response_model=ClassificationActionResponse)
async def admin_update_classification(
    class_id: int, class_data: ClassificationUpdate, current_user: User = Depends(require_super_admin)
):
    """Update a review classification (super admin only)."""
    existing = await review_classification_repository.findById(class_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classification not found")

    from app.models.daos_flat import ClassificationTagsInternalUpdate
    update_data = ClassificationTagsInternalUpdate()

    if class_data.name is not None:
        name = class_data.name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name cannot be empty")

        # Check uniqueness
        all_classes = await review_classification_repository.findAll()
        for c in all_classes:
            if c.id != class_id and (c.name or "").strip().lower() == name.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Classification name already in use"
                )
        update_data.name = name

    if class_data.is_active is not None:
        update_data.is_active = class_data.is_active

    if not update_data.model_fields_set:
        return ClassificationActionResponse(message="No changes made", classification=existing)

    updated = await review_classification_repository.update(class_id, update_data)
    return ClassificationActionResponse(message="Classification updated successfully", classification=updated or existing)
