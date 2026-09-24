from app.models.daos import ProductInternalUpdate
import uuid
from app.models.user import User
from collections import defaultdict
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.services.email_service import email_service

from app.models.daos_flat import ReturnRequestInternalUpdate, ReturnRequestInternal
from app.models.schemas import ReturnRequestCreate, ReturnRequestResponse, ReturnRequestStatus, ReturnRequestUpdate, ReturnEligibilityResponse, ReturnEligibilityItem, ReturnRequest
from app.repositories.category_repository import category_repository
from app.repositories.delivery_charge_repository import delivery_charge_repository
from app.repositories.order_repository import order_repository
from app.repositories.product_repository import product_repository
from app.repositories.return_request_repository import return_request_repository
from app.repositories.return_settings_repository import return_settings_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, require_super_admin, require_super_admin_or_valet
from app.utils.logger import logger

router = APIRouter()


async def populate_return_request(request: ReturnRequestInternal) -> ReturnRequestResponse:
    user = await user_repository.findById(request.userId) if request.userId else None
    valet = None
    if request.valetId:
        valet = await user_repository.findById(request.valetId)

    from app.models.schemas import ItemSnippet, UserSnippet, ValetSnippet
    populated_items = []
    items_list = request.items or []
    for item in items_list:
        pid = getattr(item, "productId", getattr(item, "product", None))
        product = await product_repository.findById(pid) if pid else None
        
        populated_items.append(ItemSnippet(
            productId=pid,
            product=product.name if product else "Product not found",
            quantity=getattr(item, "quantity", 0),
            price=product.price if product else 0.0,
            mrp=product.mrp if product else 0.0,
            name=product.name if product else "Unknown",
            image=product.images[0] if product and getattr(product, "images", None) else None
        ))

    response = ReturnRequestResponse.model_validate(request, from_attributes=True)
    response.items = populated_items
    
    if user:
        response.user = UserSnippet(id=user.id, name=user.name, email=user.email, phone=user.phone)
    if valet:
        response.valet = ValetSnippet(id=valet.id, name=valet.name)
        
    return response


@router.get("/my-returns", response_model=List[ReturnRequestResponse])
async def get_my_returns(current_user: User = Depends(get_current_user)):
    """Customer gets their return requests"""
    if current_user.role not in ["customer", "wholesaler"]:
        raise HTTPException(status_code=403, detail="Only customers can view their returns")

    requests = await return_request_repository.findAll({"userId": current_user.id})
    return [await populate_return_request(req) for req in requests]


@router.get("/admin/all", response_model=List[ReturnRequestResponse])
async def get_all_returns(status: Optional[str] = None, current_user: User = Depends(require_super_admin)):
    """Super admin gets all return requests"""
    query = {}
    if status:
        query["status"] = status
    requests = await return_request_repository.findAll(query)
    return [await populate_return_request(req) for req in requests]


@router.get("/valet/assigned", response_model=List[ReturnRequestResponse])
async def get_valet_returns(current_user: User = Depends(require_super_admin_or_valet)):
    """Valet gets returns assigned to them"""
    if current_user.role != "valet":
        raise HTTPException(status_code=403, detail="Only valets can view assigned returns")

    requests = await return_request_repository.findAll(
        {"valetId": current_user.id, "status": ReturnRequestStatus.ASSIGNED.value}
    )
    return [await populate_return_request(req) for req in requests]


@router.get("/order/{order_id}/eligibility", response_model=ReturnEligibilityResponse)
async def check_return_eligibility(order_id: str, current_user: User = Depends(get_current_user)):
    """Check which items in an order are eligible for return"""
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user != current_user.id and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Access denied")

    if current_user.role not in ["customer", "super_admin"]:
        return {"eligibleItems": [], "reason": "Only retail customers can return items"}

    # Must be delivered
    if order.status != "delivered":
        return {"eligibleItems": [], "reason": "Order is not delivered yet"}

    if not order.delivered_at:
        return ReturnEligibilityResponse(eligibleItems=[], reason="Delivery date not found")
        
    delivered_at = order.delivered_at
    from datetime import timezone
    if not delivered_at.tzinfo:
        delivered_at = delivered_at.replace(tzinfo=timezone.utc)

    settings = await return_settings_repository.get_settings()
    return_days = settings.returnDays if settings.returnDays is not None else 7

    if datetime.now(timezone.utc) > delivered_at + timedelta(days=return_days):
        return {"eligibleItems": [], "reason": f"Return window of {return_days} days has expired"}

    # Check for existing pending/approved returns for this order to avoid duplicates on same items
    existing_returns = await return_request_repository.findByOrderId(order_id)
    returned_items_qty = defaultdict(int)  # map of productId to quantity already returned/requested
    for req in existing_returns:
        req_status = req.status
        if req_status in [
            ReturnRequestStatus.PENDING,
            ReturnRequestStatus.ASSIGNED,
            ReturnRequestStatus.COLLECTED,
            ReturnRequestStatus.RETURNED,
        ]:
            items_list = req.items or []
            for item in (items_list or []):
                pid = item.productId
                qty = item.quantity if item.quantity is not None else 0
                if pid:
                    returned_items_qty[pid] += qty

    # Check which items are from returnable categories
    eligible_items = []
    for item in (order.items or []):
        pid = item.productId
        product = await product_repository.findById(pid)
        if not product:
            continue

        cat_name = product.category
        category = await category_repository.findByName(cat_name)

        is_returnable = category and (category.is_returnable if category.is_returnable is not None else False)

        ordered_qty = (item.quantity if item.quantity is not None else 0)
        returned_qty = returned_items_qty[pid]
        available_qty = max(0, ordered_qty - returned_qty)

        if is_returnable and available_qty > 0:
            eligible_items.append(
                {
                    "productId": pid,
                    "name": product.name,
                    "maxQuantity": available_qty,
                    "price": item.price,
                    "image": (product.images if product.images is not None else [None])[0] if product.images else None,
                }
            )

    # Calculate return delivery charge (reusing order delivery logic if possible, or computing a return charge)
    # For now, we fetch base delivery charge for customer's pincode
    delivery_charge = 0
    shipping_address = order.shipping_address
    if shipping_address:
        addr_state = shipping_address.state or ""
        addr_city = shipping_address.city or ""
        addr_district = shipping_address.district or ""
        addr_zip = shipping_address.pincode or ""
        charge_data = await delivery_charge_repository.getChargeForLocation(
            addr_state,
            addr_city,
            addr_district,
            addr_zip,
            "customer",
            0,  # total before shipping = 0 for return
        )
        if charge_data:
            delivery_charge = float(charge_data.charge or 0)

    return ReturnEligibilityResponse(
        eligibleItems=eligible_items,
        reason=None if eligible_items else "No items in this order are eligible for return",
        returnDeliveryCharge=delivery_charge,
    )


@router.post("/request", response_model=ReturnRequestResponse)
async def create_return_request(request_data: ReturnRequestCreate, current_user: User = Depends(get_current_user)):
    """Customer submits a return request"""
    if current_user.role != "customer":
        raise HTTPException(status_code=403, detail="Only retail customers can create return requests")

    eligibility = await check_return_eligibility(request_data.orderId, current_user)
    elig_model = eligibility

    eligibility_reason = elig_model.reason
    if eligibility_reason:
        raise HTTPException(status_code=400, detail=eligibility_reason)

    eligible_items_list = elig_model.eligibleItems
    eligible_items_map = {
        item.productId: item.maxQuantity
        for item in (eligible_items_list or [])
    }

    if not request_data.items:
        raise HTTPException(status_code=400, detail="No items specified for return")

    for item in request_data.items:
        if item.productId not in eligible_items_map:
            raise HTTPException(status_code=400, detail=f"Item {item.productId} is not eligible for return")
        if item.quantity > eligible_items_map[item.productId] or item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Invalid quantity for item {item.productId}")

    if request_data.paymentMethod == "upi" and not request_data.upiPaymentScreenshot:
        raise HTTPException(status_code=400, detail="UPI payment screenshot is required")

    screenshot_path = None
    if request_data.paymentMethod == "upi" and request_data.upiPaymentScreenshot:
        from app.services.oci_storage import upload_base64_image_and_return_path

        screenshot_path = await upload_base64_image_and_return_path(
            request_data.upiPaymentScreenshot, "returns", filename_prefix="return-screenshot"
        )

    delivery_charge_val = elig_model.returnDeliveryCharge or 0
    from app.models.daos import ReturnRequestInternalCreate
    created = await return_request_repository.create(
        ReturnRequestInternalCreate(
            orderId=request_data.orderId,
            userId=current_user.id,
            items=[i for i in request_data.items],
            paymentMethod=request_data.paymentMethod,
            upiPaymentScreenshot=screenshot_path,
            notes=request_data.notes,
            status=ReturnRequestStatus.PENDING.value,
            deliveryCharge=delivery_charge_val,
        )
    )

    # Notify super admin
    try:
        from app.repositories.notification_repository import notification_repository

        super_admin = await user_repository.findOne({"role": "super_admin"})
        if super_admin:
            created_model = created
            created_ret_id = str(created_model.id or "")
            import uuid
            from app.models.daos import NotificationInternalCreate
            await notification_repository.create(
                NotificationInternalCreate(
                    _id=str(uuid.uuid4()),
                    userId=super_admin.id,
                    type="new_return",
                    title="New Return Request",
                    message=f"New return request for order {request_data.orderId}",
                    metadata={
                        "returnId": created_ret_id,
                        "orderId": request_data.orderId,
                    }
                )
            )
    except Exception as e:
        logger.error("Error notifying admin for return of order %s: %s", request_data.orderId, str(e), exc_info=True)

    return await populate_return_request(created)


@router.post("/admin/{request_id}/auto-assign", response_model=ReturnRequestResponse)
async def auto_assign_return(request_id: str, current_user: User = Depends(require_super_admin)):
    """Super Admin triggers auto-assigning the return pickup to the best available valet."""
    req = await return_request_repository.findById(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Return request not found")

    from app.jobs.valet_timeout_job import _find_next_available_valet_for_return

    candidate = await _find_next_available_valet_for_return(req, [])
    if not candidate:
        raise HTTPException(
            status_code=400,
            detail="No eligible on-duty valets currently available in customer's area matching availability criteria.",
        )

    valet_id = str(candidate.id if hasattr(candidate, "id") else candidate.get("_id"))
    now_iso = datetime.utcnow().isoformat() + "Z"

    from app.models.daos_flat import ReturnRequestInternalUpdate
    updated = await return_request_repository.update(
        request_id,
        ReturnRequestInternalUpdate(
            status=ReturnRequestStatus.PENDING_VALET.value,
            pendingValetId=valet_id,
            valetAssignedAt=now_iso,
            valetCascadeCount=(req.valetCascadeCount or 0) + 1,
            valetDeclineHistory=[],
        ),
    )

    return await populate_return_request(updated)


@router.put("/admin/{request_id}/assign", response_model=ReturnRequestResponse)
async def assign_valet(
    request_id: str, valet_data: ReturnRequestUpdate, current_user: User = Depends(require_super_admin)
):
    """Super Admin assigns valet to return request"""
    if not valet_data.valetId:
        raise HTTPException(status_code=400, detail="valetId is required")

    req = await return_request_repository.findById(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Return request not found")

    v_user = await user_repository.findById(valet_data.valetId)
    if not v_user or v_user.role != "valet":
        raise HTTPException(status_code=400, detail="Valid Valet ID is required")

    updated = await return_request_repository.update(
        request_id, ReturnRequestInternalUpdate(valetId=valet_data.valetId, status=ReturnRequestStatus.ASSIGNED.value)
    )

    return await populate_return_request(updated)


@router.put("/valet/{request_id}/collect", response_model=ReturnRequestResponse)
async def valet_collect(request_id: str, current_user: User = Depends(require_super_admin_or_valet)):
    """Valet marks return as collected"""
    req = await return_request_repository.findById(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Return request not found")

    if current_user.role == "valet" and req.valet_id != current_user.id:
        raise HTTPException(status_code=403, detail="Return request not assigned to you")

    if req.status != ReturnRequestStatus.ASSIGNED.value:
        raise HTTPException(status_code=400, detail="Return request is not in ASSIGNED state")

    updated = await return_request_repository.update(request_id, ReturnRequestInternalUpdate(status=ReturnRequestStatus.COLLECTED.value))

    return await populate_return_request(updated)


@router.put("/admin/{request_id}/complete", response_model=ReturnRequestResponse)
async def complete_return(
    request_id: str, background_tasks: BackgroundTasks, current_user: User = Depends(require_super_admin)
):
    """Super Admin completes returns (marks as RETURNED) and handles stock update"""
    req = await return_request_repository.findById(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Return request not found")

    if req.status not in [ReturnRequestStatus.COLLECTED.value, ReturnRequestStatus.ASSIGNED.value]:
        raise HTTPException(status_code=400, detail="Return request must be collected first")

    updated = await return_request_repository.update(request_id, ReturnRequestInternalUpdate(status=ReturnRequestStatus.RETURNED.value))

    # Optionally: Restock items
    for item in (req.items or []):
        try:
            product = await product_repository.findById(item.product_id)
            if product:
                await product_repository.update(
                    product.id, ProductInternalUpdate(stock=(product.stock if product.stock is not None else 0) + (item.quantity if item.quantity is not None else 0))
                )
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(
                "Data error restocking product %s for return %s: %s", item.product_id, req.id, str(e)
            )
        except Exception as e:
            logger.error(
                "Unexpected error restocking product %s for return %s: %s",
                item.product_id,
                req.id,
                str(e),
                exc_info=True,
            )

    populated_req = await populate_return_request(updated)
    user_info = populated_req.user
    email = user_info.email if user_info else None
    if email:
        background_tasks.add_task(email_service.send_order_returned_email, email, populated_req)

    return populated_req


@router.put("/admin/{request_id}/reject", response_model=ReturnRequestResponse)
async def reject_return(
    request_id: str, update_data: ReturnRequestUpdate, current_user: User = Depends(require_super_admin)
):
    """Super Admin rejects the return request"""
    req = await return_request_repository.findById(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Return request not found")

    updated = await return_request_repository.update(
        request_id, ReturnRequestInternalUpdate(status=ReturnRequestStatus.REJECTED.value, notes=update_data.notes or req.notes)
    )

    return await populate_return_request(updated)


from pydantic import BaseModel

@router.get("/valet/pending", response_model=List[ReturnRequestResponse])
async def get_valet_pending_returns(current_user: User = Depends(get_current_user)):
    if current_user.role != "valet":
        raise HTTPException(status_code=403, detail="Only valets can view pending assignments")
    returns = await return_request_repository.findAll({
        "status": "pending_valet",
        "pendingValetId": str(current_user.id)
    })
    return [await populate_return_request(r) for r in returns]

class ValetReturnResponseRequest(BaseModel):
    accept: bool
    declineReason: Optional[str] = None


@router.put("/valet/{return_id}/response", response_model=ReturnRequestResponse)
async def valet_return_response(
    return_id: str,
    response_data: ValetReturnResponseRequest,
    current_user: User = Depends(get_current_user),
):
    ret = await return_request_repository.findById(return_id)
    if not ret:
        raise HTTPException(status_code=404, detail="Return request not found")

    

    if current_user.role != "super_admin":
        if current_user.role != "valet":
            raise HTTPException(status_code=403, detail="Access denied")
        pending_valet = ret.pendingValetId or ""
        if str(pending_valet or "") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Return is not assigned to you")

    current_status = ret.status
    if current_status != "pending_valet":
        raise HTTPException(status_code=400, detail="Return is not pending valet acceptance")

    from datetime import datetime, timezone

    now_iso = datetime.now(timezone.utc).isoformat() + "Z"

    if response_data.accept:
        updated_ret = await return_request_repository.update(
            return_id,
            ReturnRequestInternalUpdate(
                status="assigned",
                valetId=str(current_user.id),
                pendingValetId=None,
                valetAssignedAt=now_iso,
            ),
        )
        return await populate_return_request(updated_ret)
    else:
        # Declined -> Cascade
        from app.models.daos_flat import ReturnRequestValetDeclineInternal
        raw_history = ret.valetDeclineHistory
        history = list(raw_history or [])
        valet_id_str = str(current_user.id)
        if not any(d.valetId == valet_id_str for d in history):
            history.append(ReturnRequestValetDeclineInternal(valetId=valet_id_str, reason=response_data.declineReason))

        await return_request_repository.update(
            return_id, ReturnRequestInternalUpdate(valetDeclineHistory=history, pendingValetId=None)
        )
        ret.valetDeclineHistory = history
        ret.pendingValetId = None
        
        from app.jobs.valet_timeout_job import _cascade_or_revert_return
        await _cascade_or_revert_return(ret)
        return await populate_return_request(await return_request_repository.findById(return_id))


