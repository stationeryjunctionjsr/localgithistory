from app.models.user import User
from typing import Dict, Any, List
from app.models.schemas import MessageResponse
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.daos_flat import OrderFeedbackInternalCreate
from app.models.schemas import OrderFeedbackCreate, OrderFeedbackResponse, EligibleFeedbackResponse
from app.repositories.order_feedback_repository import order_feedback_repository
from app.repositories.order_repository import order_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=OrderFeedbackResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=OrderFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(feedback_data: OrderFeedbackCreate, current_user: User = Depends(get_current_user)):
    # Only validate order if it's order feedback
    if feedback_data.feedback_type == "order":
        if not feedback_data.order_id:
            raise HTTPException(status_code=400, detail="OrderId is required for order feedback")

        # Verify order belongs to user and is delivered
        order = await order_repository.findById(feedback_data.order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.user != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        if order.status != "delivered":
            raise HTTPException(status_code=400, detail="Order must be delivered before providing feedback")

        # Check if feedback already exists
        existing = await order_feedback_repository.findByOrder(feedback_data.order_id)
        if existing:
            raise HTTPException(status_code=400, detail="Feedback already submitted for this order")

    feedback = await order_feedback_repository.create(
        {
            "orderId": feedback_data.order_id,
            "userId": current_user.id,
            "rating": feedback_data.rating,
            "comment": feedback_data.comment or "",
            "deliveryRating": feedback_data.delivery_rating,
            "deliveryComment": feedback_data.delivery_comment or "",
            "feedbackType": feedback_data.feedback_type,
        }
    )

    return feedback


@router.get("/eligible", response_model=EligibleFeedbackResponse)
async def get_eligible_feedback_order(current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    # get all 'delivered' orders for the user
    # Wait, order_repository.findAll might not be the correct method if we don't have it.
    orders = await order_repository.findAll({"user": user_id, "status": "delivered"})

    if not orders:
        return {"eligibleOrderId": None}

    # get all feedbacks
    feedbacks = await order_feedback_repository.findByUser(user_id)

    # order orders by deliveredAt or createdAt descending
    orders.sort(key=lambda x: (x.created_at or ""), reverse=True)
    feedback_order_ids = {f.order_id for f in feedbacks if f.order_id}
    orders_without_feedback = [o for o in orders if o.id not in feedback_order_ids]

    if not orders_without_feedback:
        return {"eligibleOrderId": None}

    latest_eligible_order = orders_without_feedback[0]

    if not feedbacks:
        # User has never given feedback, and has delivered orders. Return the latest delivered order ID.
        return {"eligibleOrderId": latest_eligible_order.id}

    # User HAS given feedback
    # Get the latest feedback
    feedbacks.sort(key=lambda x: (x.created_at or ""), reverse=True)
    latest_feedback = feedbacks[0]
    from datetime import datetime, timezone

    from dateutil import parser
    from dateutil.relativedelta import relativedelta

    try:
        latest_feedback_date = parser.parse(latest_feedback.created_at) if isinstance(latest_feedback.created_at, str) else latest_feedback.created_at
        if not latest_feedback_date.tzinfo:
            latest_feedback_date = latest_feedback_date.replace(tzinfo=timezone.utc)
    except Exception:
        logger.warning(
            "Could not parse latest feedback createdAt %r for feedback %r; defaulting to now() for eligibility window.",
            latest_feedback.created_at, getattr(latest_feedback, 'id', '?'), exc_info=True,
        )
        latest_feedback_date = datetime.now(timezone.utc)

    next_eligible_date = latest_feedback_date + relativedelta(months=1)

    current_date = datetime.now(timezone.utc)

    if current_date < next_eligible_date:
        return {"eligibleOrderId": None}

    # We are past the next_eligible_date.
    return {"eligibleOrderId": latest_eligible_order.id}


@router.get("/order/{order_id}", response_model=OrderFeedbackResponse)
async def get_feedback_by_order(order_id: str, current_user: User = Depends(get_current_user)):
    feedback = await order_feedback_repository.findByOrder(order_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    # Check access
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user != current_user.id and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return feedback


@router.get("", response_model=List[OrderFeedbackResponse])
@router.get("/", response_model=List[OrderFeedbackResponse])
async def get_all_feedback(current_user: User = Depends(require_super_admin)):
    feedbacks = await order_feedback_repository.findAll()

    # populate user and order info
    for f in feedbacks:
        if f.userId:
            user = await user_repository.findById(f.userId)
            if user:
                f.user = {"name": (user.name if user.name is not None else "Unknown"), "email": (user.email or "")}

    # sort by createdAt descending
    feedbacks.sort(key=lambda x: (x.created_at or ""), reverse=True)

    return feedbacks
