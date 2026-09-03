from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.services.email_service import email_service

from app.models.schemas import ReturnRequestCreate, ReturnRequestResponse, ReturnRequestStatus, ReturnRequestUpdate
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


async def populate_return_request(request: Dict) -> Dict:
    user = await user_repository.findById(request.get("userId"))
    valet = None
    if request.get("valetId"):
        valet = await user_repository.findById(request.get("valetId"))

    populated_items = []
    for item in request.get("items", []):
        product = await product_repository.findById(item.get("productId"))
        populated_items.append(
            {**item, "product": product if product else {"_id": item.get("productId"), "name": "Product not found"}}
        )

    return {
        **request,
        "user": {
            "_id": user.get("_id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "phone": user.get("phone"),
        }
        if user
        else None,
        "valet": {"_id": valet.get("_id"), "name": valet.get("name")} if valet else None,
        "items": populated_items,
    }


@router.get("/my-returns", response_model=List[ReturnRequestResponse])
async def get_my_returns(current_user: dict = Depends(get_current_user)):
    """Customer gets their return requests"""
    if current_user.get("role") not in ["customer", "wholesaler"]:
        raise HTTPException(status_code=403, detail="Only customers can view their returns")

    requests = await return_request_repository.findAll({"userId": current_user.get("_id")})
    return [await populate_return_request(req) for req in requests]


@router.get("/admin/all", response_model=List[ReturnRequestResponse])
async def get_all_returns(status: Optional[str] = None, current_user: dict = Depends(require_super_admin)):
    """Super admin gets all return requests"""
    query = {}
    if status:
        query["status"] = status
    requests = await return_request_repository.findAll(query)
    return [await populate_return_request(req) for req in requests]


@router.get("/valet/assigned", response_model=List[ReturnRequestResponse])
async def get_valet_returns(current_user: dict = Depends(require_super_admin_or_valet)):
    """Valet gets returns assigned to them"""
    if current_user.get("role") != "valet":
        raise HTTPException(status_code=403, detail="Only valets can view assigned returns")

    requests = await return_request_repository.findAll(
        {"valetId": current_user.get("_id"), "status": ReturnRequestStatus.ASSIGNED.value}
    )
    return [await populate_return_request(req) for req in requests]


@router.get("/order/{order_id}/eligibility")
async def check_return_eligibility(order_id: str, current_user: dict = Depends(get_current_user)):
    """Check which items in an order are eligible for return"""
    order = await order_repository.findById(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.get("user") != current_user.get("_id") and current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Access denied")

    if current_user.get("role") not in ["customer", "super_admin"]:
        return {"eligibleItems": [], "reason": "Only retail customers can return items"}

    # Must be delivered
    if order.get("status") != "delivered":
        return {"eligibleItems": [], "reason": "Order is not delivered yet"}

    delivered_at_str = order.get("deliveredAt")
    if not delivered_at_str:
        return {"eligibleItems": [], "reason": "Delivery date not found"}

    try:
        delivered_at = datetime.fromisoformat(delivered_at_str.replace("Z", "+00:00"))
        if not delivered_at.tzinfo:
            delivered_at = delivered_at.replace(tzinfo=timezone.utc)
    except ValueError:
        return {"eligibleItems": [], "reason": "Malformed delivery date format"}
    except Exception as e:
        logger.error("Unexpected error parsing deliveredAt for order %s: %s", order_id, str(e), exc_info=True)
        return {"eligibleItems": [], "reason": "Error processing delivery date"}

    settings = await return_settings_repository.get_settings()
    return_days = settings.get("returnDays", 7)

    if datetime.now(timezone.utc) > delivered_at + timedelta(days=return_days):
        return {"eligibleItems": [], "reason": f"Return window of {return_days} days has expired"}

    # Check for existing pending/approved returns for this order to avoid duplicates on same items
    existing_returns = await return_request_repository.findByOrderId(order_id)
    returned_items_qty = {}  # map of productId to quantity already returned/requested
    for req in existing_returns:
        if req.get("status") in [
            ReturnRequestStatus.PENDING,
            ReturnRequestStatus.ASSIGNED,
            ReturnRequestStatus.COLLECTED,
            ReturnRequestStatus.RETURNED,
        ]:
            for item in req.get("items", []):
                pid = item.get("productId")
                returned_items_qty[pid] = returned_items_qty.get(pid, 0) + item.get("quantity", 0)

    # Check which items are from returnable categories
    eligible_items = []
    for item in order.get("items", []):
        pid = item.get("product")
        product = await product_repository.findById(pid)
        if not product:
            continue

        cat_name = product.get("category")
        category = await category_repository.findByName(cat_name)

        is_returnable = category and category.get("isReturnable", False)

        ordered_qty = item.get("quantity", 0)
        returned_qty = returned_items_qty.get(pid, 0)
        available_qty = max(0, ordered_qty - returned_qty)

        if is_returnable and available_qty > 0:
            eligible_items.append(
                {
                    "productId": pid,
                    "name": product.get("name"),
                    "maxQuantity": available_qty,
                    "price": item.get("price"),
                    "image": product.get("images", [None])[0] if product.get("images") else None,
                }
            )

    # Calculate return delivery charge (reusing order delivery logic if possible, or computing a return charge)
    # For now, we fetch base delivery charge for customer's pincode
    delivery_charge = 0
    shipping_address = order.get("shippingAddress", {})
    if shipping_address:
        charge_data = await delivery_charge_repository.getChargeForLocation(
            shipping_address.get("state", ""),
            shipping_address.get("city", ""),
            shipping_address.get("district", ""),
            shipping_address.get("zipCode", ""),
            "customer",
            0,  # total before shipping = 0 for return
        )
        if charge_data:
            delivery_charge = float(charge_data.get("charge", 0))

    return {
        "eligibleItems": eligible_items,
        "reason": None if eligible_items else "No items in this order are eligible for return",
        "returnDeliveryCharge": delivery_charge,
    }


@router.post("/request", response_model=ReturnRequestResponse)
async def create_return_request(request_data: ReturnRequestCreate, current_user: dict = Depends(get_current_user)):
    """Customer submits a return request"""
    if current_user.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Only retail customers can create return requests")

    eligibility = await check_return_eligibility(request_data.orderId, current_user)

    if eligibility.get("reason"):
        raise HTTPException(status_code=400, detail=eligibility["reason"])

    eligible_items_map = {item["productId"]: item["maxQuantity"] for item in eligibility["eligibleItems"]}

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

    created = await return_request_repository.create(
        {
            "orderId": request_data.orderId,
            "userId": current_user.get("_id"),
            "items": [i.dict() for i in request_data.items],
            "paymentMethod": request_data.paymentMethod,
            "upiPaymentScreenshot": screenshot_path,
            "notes": request_data.notes,
            "status": ReturnRequestStatus.PENDING.value,
            "deliveryCharge": eligibility.get("returnDeliveryCharge", 0),
        }
    )

    # Notify super admin
    try:
        from app.repositories.notification_repository import notification_repository

        super_admin = await user_repository.findOne({"role": "super_admin"})
        if super_admin:
            await notification_repository.create(
                {
                    "userId": super_admin.get("_id"),
                    "type": "new_return",
                    "title": "New Return Request",
                    "message": f"New return request for order {request_data.orderId}",
                    "data": {
                        "returnId": created.get("_id"),
                        "orderId": request_data.orderId,
                    },
                }
            )
    except Exception as e:
        logger.error("Error notifying admin for return of order %s: %s", request_data.orderId, str(e), exc_info=True)

    return await populate_return_request(created)


@router.post("/admin/{request_id}/auto-assign", response_model=ReturnRequestResponse)
async def auto_assign_return(request_id: str, current_user: dict = Depends(require_super_admin)):
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

    valet_id = str(candidate["_id"])
    now_iso = datetime.utcnow().isoformat() + "Z"

    updated = await return_request_repository.update(
        request_id,
        {
            "status": ReturnRequestStatus.PENDING_VALET.value,
            "pendingValetId": valet_id,
            "valetId": None,
            "valetAssignedAt": now_iso,
            "valetDeclineHistory": [],
            "valetCascadeCount": 0,
        },
    )

    return await populate_return_request(updated)


@router.put("/admin/{request_id}/assign", response_model=ReturnRequestResponse)
async def assign_valet(
    request_id: str, valet_data: ReturnRequestUpdate, current_user: dict = Depends(require_super_admin)
):
    """Super Admin assigns valet to return request"""
    if not valet_data.valetId:
        raise HTTPException(status_code=400, detail="valetId is required")

    req = await return_request_repository.findById(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Return request not found")

    v_user = await user_repository.findById(valet_data.valetId)
    if not v_user or v_user.get("role") != "valet":
        raise HTTPException(status_code=400, detail="Valid Valet ID is required")

    updated = await return_request_repository.update(
        request_id, {"valetId": valet_data.valetId, "status": ReturnRequestStatus.ASSIGNED.value}
    )

    return await populate_return_request(updated)


@router.put("/valet/{request_id}/collect", response_model=ReturnRequestResponse)
async def valet_collect(request_id: str, current_user: dict = Depends(require_super_admin_or_valet)):
    """Valet marks return as collected"""
    req = await return_request_repository.findById(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Return request not found")

    if current_user.get("role") == "valet" and req.get("valetId") != current_user.get("_id"):
        raise HTTPException(status_code=403, detail="Return request not assigned to you")

    if req.get("status") != ReturnRequestStatus.ASSIGNED.value:
        raise HTTPException(status_code=400, detail="Return request is not in ASSIGNED state")

    updated = await return_request_repository.update(request_id, {"status": ReturnRequestStatus.COLLECTED.value})

    return await populate_return_request(updated)


@router.put("/admin/{request_id}/complete", response_model=ReturnRequestResponse)
async def complete_return(
    request_id: str, background_tasks: BackgroundTasks, current_user: dict = Depends(require_super_admin)
):
    """Super Admin completes returns (marks as RETURNED) and handles stock update"""
    req = await return_request_repository.findById(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Return request not found")

    if req.get("status") not in [ReturnRequestStatus.COLLECTED.value, ReturnRequestStatus.ASSIGNED.value]:
        raise HTTPException(status_code=400, detail="Return request must be collected first")

    updated = await return_request_repository.update(request_id, {"status": ReturnRequestStatus.RETURNED.value})

    # Optionally: Restock items
    for item in req.get("items", []):
        try:
            product = await product_repository.findById(item.get("productId"))
            if product:
                await product_repository.update(
                    product.get("_id"), {"stock": product.get("stock", 0) + item.get("quantity", 0)}
                )
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(
                "Data error restocking product %s for return %s: %s", item.get("productId"), req.get("_id"), str(e)
            )
        except Exception as e:
            logger.error(
                "Unexpected error restocking product %s for return %s: %s",
                item.get("productId"),
                req.get("_id"),
                str(e),
                exc_info=True,
            )

    populated_req = await populate_return_request(updated)
    email = populated_req.get("user", {}).get("email") if populated_req.get("user") else None
    if email:
        background_tasks.add_task(email_service.send_order_returned_email, email, populated_req)

    return populated_req


@router.put("/admin/{request_id}/reject", response_model=ReturnRequestResponse)
async def reject_return(
    request_id: str, update_data: ReturnRequestUpdate, current_user: dict = Depends(require_super_admin)
):
    """Super Admin rejects the return request"""
    req = await return_request_repository.findById(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Return request not found")

    updated = await return_request_repository.update(
        request_id, {"status": ReturnRequestStatus.REJECTED.value, "notes": update_data.notes or req.get("notes")}
    )

    return await populate_return_request(updated)


from pydantic import BaseModel

@router.get("/valet/pending")
async def get_valet_pending_returns(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "valet":
        raise HTTPException(status_code=403, detail="Only valets can view pending assignments")
    returns = await return_request_repository.findAll({
        "status": "pending_valet",
        "pendingValetId": str(current_user["_id"])
    })
    return [await populate_return_request(r) for r in returns]

class ValetReturnResponseRequest(BaseModel):
    accept: bool
    declineReason: Optional[str] = None

@router.put("/valet/{return_id}/response", response_model=dict)
async def valet_return_response(
    return_id: str,
    response_data: ValetReturnResponseRequest,
    current_user: dict = Depends(get_current_user),
):
    ret = await return_request_repository.findById(return_id)
    if not ret:
        raise HTTPException(status_code=404, detail="Return request not found")
        
    if current_user.get("role") != "super_admin":
        if current_user.get("role") != "valet":
            raise HTTPException(status_code=403, detail="Access denied")
        if str(ret.get("pendingValetId", "")) != str(current_user["_id"]):
            raise HTTPException(status_code=403, detail="Return is not assigned to you")
            
    if ret.get("status") != "pending_valet":
        raise HTTPException(status_code=400, detail="Return is not pending valet acceptance")
        
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat() + "Z"
    
    if response_data.accept:
        updated_ret = await return_request_repository.update(return_id, {
            "status": "assigned",
            "valetId": str(current_user["_id"]),
            "pendingValetId": None,
            "valetAssignedAt": now_iso
        })
        return await populate_return_request(updated_ret)
    else:
        # Declined -> Cascade
        history = list(ret.get("valetDeclineHistory") or [])
        valet_id_str = str(current_user.get("_id"))
        if valet_id_str not in history:
            history.append(valet_id_str)
            
        await return_request_repository.update(return_id, {
            "valetDeclineHistory": history,
            "pendingValetId": None
        })
        ret["valetDeclineHistory"] = history
        ret["pendingValetId"] = None
        
        from app.jobs.valet_timeout_job import _cascade_or_revert_return
        await _cascade_or_revert_return(ret)
        return await populate_return_request(await return_request_repository.findById(return_id))

