"""
Valet Timeout Job

Scans all orders in `pending_valet` status (5 min urgent, 20 min normal) and
all return requests in `pending_valet` status (strictly 20 min normal) every minute.
If the acceptance window has expired, the job auto-cascades to the next eligible valet
or reverts to `processing`/`pending` and notifies the seller/admin.
"""

from datetime import datetime, timedelta, timezone

from app.repositories.order_repository import order_repository
from app.repositories.return_request_repository import return_request_repository
from app.repositories.user_repository import user_repository
from app.utils.logger import logger

URGENT_TIMEOUT_MINUTES = 5
NORMAL_TIMEOUT_MINUTES = 20


async def _cascade_or_revert(order: dict):
    """
    Try to offer the order to the next best valet.
    If no valets are available, revert to 'processing' and notify the seller.
    """
    order_id = str(order["_id"])
    seller_id = order.get("sellerId")
    is_urgent = order.get("isUrgentDelivery", False)
    declined_history = order.get("valetDeclineHistory", [])

    # ── Build next candidate ──────────────────────────────────────────────────
    next_valet = await _find_next_available_valet(order, declined_history)

    now_iso = datetime.now(timezone.utc).isoformat()

    if next_valet:
        next_valet_id = str(next_valet["_id"])
        cascade_count = (order.get("valetCascadeCount") or 0) + 1

        await order_repository.update(
            order_id,
            {
                "pendingValetId": next_valet_id,
                "valetAssignedAt": now_iso,
                "valetCascadeCount": cascade_count,
                "valetDeclineHistory": declined_history,  # already includes timed-out valet
            },
        )

        # Notify next valet
        try:
            from app.services.push_notification_service import push_notification_service

            timeout_label = "5 minutes" if is_urgent else "20 minutes"
            await push_notification_service.send_to_user(
                next_valet_id,
                {
                    "title": "New Delivery Request",
                    "message": (
                        f"You have a new delivery order #{order.get('orderNumber', order_id)}. "
                        f"Please respond within {timeout_label}."
                    ),
                    "link": f"/valet/orders/{order_id}",
                    "data": {
                        "orderId": order_id,
                        "type": "valet_assignment",
                        "isUrgent": is_urgent,
                    },
                },
            )
        except Exception as e:
            logger.error("[ValetTimeout] Failed to notify next valet %s: %s", next_valet_id, e)

        logger.info(
            "[ValetTimeout] Order %s cascaded to valet %s (cascade #%d)", order_id, next_valet_id, cascade_count
        )

    else:
        # No valets left — revert to processing
        await order_repository.update(
            order_id,
            {
                "status": "processing",
                "pendingValetId": None,
                "valetAssignedAt": None,
                "valetCascadeCount": (order.get("valetCascadeCount") or 0) + 1,
            },
        )

        # Notify seller
        if seller_id:
            try:
                from app.services.push_notification_service import push_notification_service

                await push_notification_service.send_to_user(
                    seller_id,
                    {
                        "title": "Valet Unavailable — Reassign Required",
                        "message": (
                            f"No valets accepted order #{order.get('orderNumber', order_id)}. Please reassign manually."
                        ),
                        "link": f"/seller/orders/{order_id}",
                        "data": {
                            "orderId": order_id,
                            "type": "valet_all_declined",
                        },
                    },
                )
            except Exception as e:
                logger.error("[ValetTimeout] Failed to notify seller %s: %s", seller_id, e)

        logger.info("[ValetTimeout] Order %s reverted to processing — no valets available", order_id)


async def _find_next_available_valet(order: dict, skip_valet_ids: list) -> dict | None:
    """
    Find the next best eligible valet for this order, skipping already-declined ones.
    Applies the same 4-step filter as GET /valets/available and sorts by active order count.

    For multi-seller (split) orders the valet must cover ALL sellers' pincodes.
    For single-seller orders the existing behaviour is preserved.
    """
    from datetime import date as dt_date

    from app.db.storage_factory import get_storage

    today = dt_date.today().isoformat()
    slot_id = order.get("deliverySlotId")

    # ── Determine required pincodes ───────────────────────────────────────────────
    # NOTE: hasSubOrders/subOrderIds are not stored in the relational DB.
    # Instead, query sub-orders by parent ID — presence of rows means multi-seller.
    required_pincodes: set[str] = set()

    from app.repositories.sub_order_repository import sub_order_repository

    sub_orders = await sub_order_repository.findByParentOrder(str(order["_id"]))

    if sub_orders:
        # Multi-seller: collect pincodes for every sub-order's seller
        for so in sub_orders:
            so_seller_id = so.get("sellerId")
            if so_seller_id:
                so_seller = await user_repository.findById(so_seller_id)
            else:
                so_seller = await user_repository.findOne({"role": "super_admin"})
            if so_seller:
                so_addr = so_seller.get("address") or {}
                pincode = str(so_addr.get("zipCode") or so_addr.get("pincode") or "")
                if pincode:
                    required_pincodes.add(pincode)
    else:
        # Single-seller: use the order's own sellerId
        seller_id = order.get("sellerId")
        if seller_id:
            seller = await user_repository.findById(seller_id)
        else:
            seller = await user_repository.findOne({"role": "super_admin"})
        if not seller:
            return None
        seller_address = seller.get("address") or {}
        pincode = str(seller_address.get("zipCode") or seller_address.get("pincode") or "")
        if pincode:
            required_pincodes.add(pincode)

    if not required_pincodes:
        return None

    # Resolve required_pincodes to required_zones
    required_zones = set()
    from app.repositories.zone_seller_cache import get_zone_for_pincode

    for pin in required_pincodes:
        zone_doc = await get_zone_for_pincode(pin)
        if zone_doc:
            required_zones.add(str(zone_doc["_id"]))

    # Step 1+2: Get all on-duty valets
    all_valets = await user_repository.findAll({"role": "valet", "isOnDuty": True})

    # Build skip set — skip_valet_ids may be a list of dicts {"valetId": ...} or plain strings
    skip_ids: set[str] = set()
    for entry in skip_valet_ids:
        if isinstance(entry, dict):
            vid = entry.get("valetId")
            if vid:
                skip_ids.add(str(vid))
        else:
            skip_ids.add(str(entry))

    # Filter out already-declined/timed-out valets
    eligible_valets = [v for v in all_valets if str(v["_id"]) not in skip_ids]
    if not eligible_valets:
        return None

    # Step 3+4: Availability filter and Zone filter
    availability_storage = get_storage("valetAvailability")
    availability_docs = await availability_storage.findAll({"date": today})
    avail_map: dict[str, dict] = {doc["valetId"]: doc for doc in availability_docs}

    available_valets = []
    for v in eligible_valets:
        vid = str(v["_id"])
        avail = avail_map.get(vid)
        if not avail:
            continue

        # Check if valet is available for all required zones today
        valet_daily_zones = set(avail.get("zones") or [])
        if required_zones and not required_zones.issubset(valet_daily_zones):
            continue

        if avail["availabilityType"] == "full_day":
            available_valets.append(v)
        elif slot_id and slot_id in avail.get("slots", []):
            available_valets.append(v)

    if not available_valets:
        return None

    # Fetch global max concurrent orders
    sys_storage = get_storage("systemSettings")
    sys_doc = await sys_storage.findById("global_settings")
    global_max = int(sys_doc.get("maxConcurrentOrders", 1)) if sys_doc else 1

    # Step 5: Capacity + load sort — one query for ALL valets, not one per valet.
    # Previously this fired len(available_valets) separate DB queries every minute.
    BUSY_STATUSES = ["pending_valet", "shipped", "return_pickup"]
    available_valet_ids = [str(v["_id"]) for v in available_valets]

    all_active_orders = await order_repository.findAll(
        {"assignedValet": {"$in": available_valet_ids}, "status": {"$in": BUSY_STATUSES}}
    )
    # Group by valet ID in Python — O(orders) instead of O(valets × queries)
    order_count_by_valet: dict[str, int] = {}
    for o in all_active_orders:
        vid = str(o.get("assignedValet", ""))
        order_count_by_valet[vid] = order_count_by_valet.get(vid, 0) + 1

    scored = []
    for v in available_valets:
        vid = str(v["_id"])
        active_count = order_count_by_valet.get(vid, 0)
        max_concurrent = int(v.get("maxConcurrentOrders") or global_max)
        if active_count < max_concurrent:
            scored.append((active_count, v))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0])
    return scored[0][1]


async def _find_next_available_valet_for_return(return_req: dict, skip_valet_ids: list) -> dict | None:
    """
    Find the next best eligible valet for a return pickup.
    - Customer Pincode: Extracted from parent order shipping address.
    - Routing Mode:
      - Delivery Slot Flow: If product's seller has allowDeliverySlots=True and a slot was specified,
        valet must be available for that slot on the date.
      - Normal Flow (Without Slot Confirmation): If seller does not use slots / no slot specified,
        any on-duty valet available for today serving customer's pincode is eligible.
    - Capacity: active forward orders + active return pickups < maxConcurrentOrders.
    """
    from datetime import date as dt_date

    from app.db.storage_factory import get_storage
    from app.repositories.product_repository import product_repository

    order_id = return_req.get("orderId")
    order = await order_repository.findById(order_id) if order_id else None
    if not order:
        return None

    shipping_address = order.get("shippingAddress") or {}
    customer_pincode = str(shipping_address.get("zipCode") or shipping_address.get("pincode") or "")
    if not customer_pincode:
        user = await user_repository.findById(return_req.get("userId")) if return_req.get("userId") else None
        if user and getattr(user, "address", {}):
            customer_pincode = str(getattr(user, "address", {}).get("pincode") or getattr(user, "address", {}).get("zipCode") or "")

    if not customer_pincode:
        return None

    # Determine seller and slot configuration
    seller_id = return_req.get("sellerId")
    if not seller_id:
        # Resolve from first product or order
        items = return_req.get("items") or []
        if items:
            p_id = items[0].get("productId")
            prod = await product_repository.findById(p_id) if p_id else None
            if prod:
                seller_id = prod.get("sellerId")
        if not seller_id:
            seller_id = order.get("sellerId")

    if seller_id:
        seller = await user_repository.findById(seller_id)
    else:
        seller = await user_repository.findOne({"role": "super_admin"})

    seller_perms = (seller.get("sellerPermissions") or {}) if seller else {}
    
    slot_id = return_req.get("deliverySlotId")
    slot_date = return_req.get("deliverySlotDate") or dt_date.today().isoformat()

    # Step 1+2: Get all on-duty valets
    all_valets = await user_repository.findAll({"role": "valet", "isOnDuty": True})

    # Build skip set — skip_valet_ids may be dicts {"valetId": ...} or plain strings
    skip_ids: set[str] = set()
    for entry in skip_valet_ids:
        if isinstance(entry, dict):
            vid = entry.get("valetId")
            if vid:
                skip_ids.add(str(vid))
        else:
            skip_ids.add(str(entry))

    eligible_valets = [v for v in all_valets if str(v["_id"]) not in skip_ids]
    if not eligible_valets:
        return None

    # Step 3: Resolve customer pincode → zone (same as forward orders)
    from app.repositories.zone_seller_cache import get_zone_for_pincode

    zone_doc = await get_zone_for_pincode(customer_pincode)
    if not zone_doc:
        logger.warning(
            "[ValetTimeout] Return %s: customer pincode %s not in any zone — cannot route",
            return_req.get("_id"),
            customer_pincode,
        )
        return None
    customer_zone_id = str(zone_doc["_id"])

    # Step 4: Availability filter + zone check
    availability_storage = get_storage("valetAvailability")
    query_date = slot_date if slot_id else dt_date.today().isoformat()
    availability_docs = await availability_storage.findAll({"date": query_date})
    avail_map: dict[str, dict] = {doc["valetId"]: doc for doc in availability_docs}

    available_valets = []
    for v in eligible_valets:
        vid = str(v["_id"])
        avail = avail_map.get(vid)
        if not avail:
            continue

        # Valet must cover the customer's zone today
        valet_daily_zones = set(avail.get("zones") or [])
        if customer_zone_id not in valet_daily_zones:
            continue

        if slot_id:
            # Slot-based flow: valet must be full_day or have the matching slot
            if avail.get("availabilityType") == "full_day" or slot_id in avail.get("slots", []):
                available_valets.append(v)
        else:
            # Normal flow: full_day or has any marked slots
            if avail.get("availabilityType") == "full_day" or len(avail.get("slots", [])) > 0:
                available_valets.append(v)

    if not available_valets:
        return None

    # Fetch global max concurrent orders
    sys_storage = get_storage("systemSettings")
    sys_doc = await sys_storage.findById("global_settings")
    global_max = int(sys_doc.get("maxConcurrentOrders", 1)) if sys_doc else 1

    # Step 5: Capacity + load sort — one query per collection, not one per valet.
    BUSY_STATUSES = ["pending_valet", "shipped", "return_pickup"]
    ACTIVE_RETURN_STATUSES = ["pending_valet", "assigned"]
    available_valet_ids = [str(v["_id"]) for v in available_valets]

    # Single batched order query for all valets
    all_active_orders = await order_repository.findAll(
        {"assignedValet": {"$in": available_valet_ids}, "status": {"$in": BUSY_STATUSES}}
    )
    order_count_by_valet: dict[str, int] = {}
    for o in all_active_orders:
        vid = str(o.get("assignedValet", ""))
        order_count_by_valet[vid] = order_count_by_valet.get(vid, 0) + 1

    # Status-filtered return query (previously fetched the entire table)
    all_active_returns = await return_request_repository.findAll({"status": {"$in": ACTIVE_RETURN_STATUSES}})
    return_count_by_valet: dict[str, int] = {}
    for r in all_active_returns:
        for key in ("valetId", "pendingValetId"):
            vid = str(r.get(key) or "")
            if vid:
                return_count_by_valet[vid] = return_count_by_valet.get(vid, 0) + 1

    scored = []
    for v in available_valets:
        vid = str(v["_id"])
        total_active_load = order_count_by_valet.get(vid, 0) + return_count_by_valet.get(vid, 0)
        max_concurrent = int(v.get("maxConcurrentOrders") or global_max)
        if total_active_load < max_concurrent:
            scored.append((total_active_load, v))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0])
    return scored[0][1]


async def _cascade_or_revert_return(return_req: dict):
    """
    Cascade return pickup offer to the next best valet or revert to 'pending'
    and notify Super Admin / Seller.
    """
    req_id = str(return_req.get("_id") or return_req.get("id"))
    declined_history = list(return_req.get("valetDeclineHistory") or [])

    next_valet = await _find_next_available_valet_for_return(return_req, declined_history)
    now_iso = datetime.now(timezone.utc).isoformat()

    if next_valet:
        next_valet_id = str(next_valet["_id"])
        cascade_count = (return_req.get("valetCascadeCount") or 0) + 1

        await return_request_repository.update(
            req_id,
            {
                "status": "pending_valet",
                "pendingValetId": next_valet_id,
                "valetAssignedAt": now_iso,
                "valetCascadeCount": cascade_count,
                "valetDeclineHistory": declined_history,
            },
        )

        # Push notification to next valet
        try:
            from app.services.push_notification_service import push_notification_service

            return_num = return_req.get("returnId", req_id)
            await push_notification_service.send_to_user(
                next_valet_id,
                {
                    "title": "New Return Pickup Request",
                    "message": (
                        f"You have a new return pickup request #{return_num}. Please respond within 20 minutes."
                    ),
                    "link": "/valet",
                    "data": {
                        "returnId": req_id,
                        "type": "valet_return_assignment",
                        "timeoutMinutes": 20,
                    },
                },
            )
        except Exception as e:
            logger.error("[ValetTimeout] Failed to notify next valet for return %s: %s", next_valet_id, e)

        logger.info("[ValetTimeout] Return %s cascaded to valet %s (cascade #%d)", req_id, next_valet_id, cascade_count)

    else:
        # Revert return request to pending
        await return_request_repository.update(
            req_id,
            {
                "status": "pending",
                "pendingValetId": None,
                "valetAssignedAt": None,
                "valetCascadeCount": (return_req.get("valetCascadeCount") or 0) + 1,
            },
        )

        # Notify Super Admin
        try:
            from app.services.push_notification_service import push_notification_service

            super_admin = await user_repository.findOne({"role": "super_admin"})
            return_num = return_req.get("returnId", req_id)
            if super_admin:
                await push_notification_service.send_to_user(
                    str(super_admin["_id"]),
                    {
                        "title": "Return Valet Unavailable — Reassign Required",
                        "message": (f"No valets accepted return pickup #{return_num}. Please reassign manually."),
                        "link": "/admin/returns-management",
                        "data": {
                            "returnId": req_id,
                            "type": "valet_return_all_declined",
                        },
                    },
                )
        except Exception as e:
            logger.error("[ValetTimeout] Failed to notify admin for return %s: %s", req_id, e)

        logger.info("[ValetTimeout] Return %s reverted to pending — no valets available", req_id)


async def run_valet_timeout_job():
    """Entry point called by the scheduler every 1 minute for both forward orders and returns."""
    try:
        # ── 1. Forward orders in pending_valet status ──────────────────────────
        pending_orders = await order_repository.findAll({"status": "pending_valet"})
        # Use timezone-aware UTC now so comparisons with stored ISO timestamps
        # (which may carry +00:00 / Z) never raise TypeError.
        now = datetime.now(timezone.utc)

        if pending_orders:
            for order in pending_orders:
                assigned_at_str = order.get("valetAssignedAt")
                if not assigned_at_str:
                    continue

                try:
                    assigned_at = datetime.fromisoformat(assigned_at_str.replace("Z", "+00:00"))
                    # Ensure aware — guard against legacy naive values stored without offset
                    if assigned_at.tzinfo is None:
                        assigned_at = assigned_at.replace(tzinfo=timezone.utc)
                except (ValueError, AttributeError):
                    continue

                is_urgent = order.get("isUrgentDelivery", False)
                timeout_minutes = URGENT_TIMEOUT_MINUTES if is_urgent else NORMAL_TIMEOUT_MINUTES
                deadline = assigned_at + timedelta(minutes=timeout_minutes)

                if now >= deadline:
                    pending_valet_id = order.get("pendingValetId")
                    if pending_valet_id:
                        history = list(order.get("valetDeclineHistory") or [])
                        if not any(isinstance(d, dict) and d.get("valetId") == pending_valet_id for d in history):
                            history.append({"valetId": pending_valet_id, "reason": "timeout"})
                        order["valetDeclineHistory"] = history

                        await order_repository.update(
                            str(order["_id"]),
                            {
                                "valetDeclineHistory": history,
                                "pendingValetId": None,
                            },
                        )
                        order = await order_repository.findById(str(order["_id"]))

                    await _cascade_or_revert(order)

        # ── 2. Return pickups in pending_valet status (strictly 20 min normal) ──
        pending_returns = await return_request_repository.findAll({"status": "pending_valet"})
        if pending_returns:
            for ret in pending_returns:
                assigned_at_str = ret.get("valetAssignedAt")
                if not assigned_at_str:
                    continue

                try:
                    assigned_at = datetime.fromisoformat(assigned_at_str.replace("Z", "+00:00"))
                    if assigned_at.tzinfo is None:
                        assigned_at = assigned_at.replace(tzinfo=timezone.utc)
                except (ValueError, AttributeError):
                    continue

                # Returns never use urgent flow — strictly 20 minutes normal timeout
                deadline = assigned_at + timedelta(minutes=NORMAL_TIMEOUT_MINUTES)

                if now >= deadline:
                    req_id = str(ret.get("_id") or ret.get("id"))
                    pending_valet_id = ret.get("pendingValetId")
                    if pending_valet_id:
                        history = list(ret.get("valetDeclineHistory") or [])
                        if not any(isinstance(d, dict) and d.get("valetId") == pending_valet_id for d in history):
                            history.append({"valetId": pending_valet_id, "reason": "timeout"})
                        ret["valetDeclineHistory"] = history

                        await return_request_repository.update(
                            req_id,
                            {
                                "valetDeclineHistory": history,
                                "pendingValetId": None,
                            },
                        )
                        ret = await return_request_repository.findById(req_id)

                    await _cascade_or_revert_return(ret)

    except Exception as e:
        logger.error("[ValetTimeout] Unexpected error in timeout job: %s", e, exc_info=True)
