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
from app.models.order import OrderInternalUpdate
from app.models.daos import OrderFilter, ValetAvailabilityFilter
from app.models.daos_flat import ReturnRequestInternalUpdate
from app.repositories.user_repository import user_repository
from app.models.user import UserFilter
from app.models.schemas import PushNotificationPayload, PushNotificationMetadata
from app.utils.logger import logger
URGENT_TIMEOUT_MINUTES = 5
NORMAL_TIMEOUT_MINUTES = 20

async def _cascade_or_revert(order):
    """
    Try to offer the order to the next best valet.
    If no valets are available, revert to 'processing' and notify the seller.
    """
    order_id = str(order.id)
    seller_id = order.seller_id
    is_urgent = order.is_urgent_delivery
    declined_history = list(order.valet_decline_history or [])
    next_valet = await _find_next_available_valet(order, declined_history)
    now_iso = datetime.now(timezone.utc).isoformat()
    if next_valet:
        next_valet_id = str(next_valet.id)
        cascade_count = ((order.valet_cascade_count) or 0) + 1
        await order_repository.update(order_id, OrderInternalUpdate(pendingValetId=next_valet_id, valetAssignedAt=now_iso, valetCascadeCount=cascade_count, valetDeclineHistory=declined_history))
        try:
            from app.services.push_notification_service import push_notification_service
            timeout_label = '5 minutes' if is_urgent else '20 minutes'
            await push_notification_service.send_to_user(
                next_valet_id,
                PushNotificationPayload(
                    title='New Delivery Request',
                    message=f"You have a new delivery order #{(order.order_number or order_id)}. Please respond within {timeout_label}.",
                    link=f'/valet/orders/{order_id}',
                    data=PushNotificationMetadata(order_id=order.id, type='valet_assignment', is_urgent=is_urgent),
                ),
            )
        except Exception as e:
            logger.error('[ValetTimeout] Failed to notify next valet %s: %s', next_valet_id, e)
        logger.info('[ValetTimeout] Order %s cascaded to valet %s (cascade #%d)', order_id, next_valet_id, cascade_count)
    else:
        await order_repository.update(order_id, OrderInternalUpdate(status='processing', pendingValetId=None, valetAssignedAt=None, valetCascadeCount=((order.valet_cascade_count) or 0) + 1))
        if seller_id:
            try:
                from app.services.push_notification_service import push_notification_service
                await push_notification_service.send_to_user(
                    seller_id,
                    PushNotificationPayload(
                        title='Valet Unavailable — Reassign Required',
                        message=f"No valets accepted order #{(order.order_number or order_id)}. Please reassign manually.",
                        link=f'/seller/orders/{order_id}',
                        data=PushNotificationMetadata(order_id=order.id, type='valet_all_declined'),
                    ),
                )
            except Exception as e:
                logger.error('[ValetTimeout] Failed to notify seller %s: %s', seller_id, e)
        logger.info('[ValetTimeout] Order %s reverted to processing — no valets available', order_id)

async def _find_next_available_valet(order, skip_valet_ids: list):
    """
    Find the next best eligible valet for this order, skipping already-declined ones.
    Applies the same 4-step filter as GET /valets/available and sorts by active order count.

    For multi-seller (split) orders the valet must cover ALL sellers' pincodes.
    For single-seller orders the existing behaviour is preserved.
    """
    from datetime import date as dt_date
    from app.db.storage_factory import get_storage
    today = dt_date.today().isoformat()
    slot_id = order.delivery_slot_id
    required_pincodes: set[str] = set()
    from app.repositories.sub_order_repository import sub_order_repository
    sub_orders = await sub_order_repository.findByParentOrder(order.id)
    if sub_orders:
        for so in sub_orders:
            so_seller_id = so.seller_id
            if so_seller_id:
                so_seller = await user_repository.findById(so_seller_id)
            else:
                so_seller = await user_repository.findSuperAdmin()
            if so_seller:
                so_addr = so_seller.address
                pincode = str((so_addr.zip_code or so_addr.pincode or '') if so_addr else '')
                if pincode:
                    required_pincodes.add(pincode)
    else:
        seller_id = order.seller_id
        if seller_id:
            seller = await user_repository.findById(seller_id)
        else:
            seller = await user_repository.findSuperAdmin()
        if not seller:
            return None
        seller_address = seller.address
        pincode = str((seller_address.zip_code or seller_address.pincode or '') if seller_address else '')
        if pincode:
            required_pincodes.add(pincode)
    if not required_pincodes:
        return None
    required_zones = set()
    from app.repositories.zone_seller_cache import get_zone_for_pincode
    for pin in required_pincodes:
        zone = await get_zone_for_pincode(pin)
        if zone:
            required_zones.add(str(zone.id))
    all_valets = await user_repository.findAll(UserFilter(role='valet', is_on_duty=True))
    print(f"DEBUG: all_valets={len(all_valets)}")
    skip_ids: set[str] = set()
    for entry in skip_valet_ids:
        vid = entry
        if vid:
            skip_ids.add(str(vid))
        else:
            skip_ids.add(str(entry))
    eligible_valets = [v for v in all_valets if str(v.id) not in skip_ids]
    print(f"DEBUG: eligible_valets={len(eligible_valets)}")
    if not eligible_valets:
        return None
    availability_storage = get_storage('valetAvailability')
    availability_records = await availability_storage.findAll(ValetAvailabilityFilter(date=today))
    available_valets = []
    for v in eligible_valets:
        vid = str(v.id)
        avail = next((rec for rec in availability_records if str(rec.valet_id) == vid), None)
        if not avail:
            continue
        valet_daily_zones = set(avail.zones or [])
        if required_zones and (not required_zones.issubset(valet_daily_zones)):
            continue
        if avail.availability_type == 'full_day':
            available_valets.append(v)
        elif slot_id and slot_id in (avail.slots):
            available_valets.append(v)
    print(f"DEBUG: available_valets={len(available_valets)}")
    if not available_valets:
        return None
    sys_storage = get_storage('systemSettings')
    sys_settings = await sys_storage.findById(1)
    global_max = (sys_settings.max_concurrent_orders or 1) if sys_settings else 1
    BUSY_STATUSES = ['pending_valet', 'shipped', 'return_pickup']
    available_valet_ids = [str(v.id) for v in available_valets]
    active_orders = await order_repository.findAll(OrderFilter(statuses=BUSY_STATUSES))
    all_active_orders = [o for o in active_orders if str(o.assigned_valet or '') in available_valet_ids]
    scored = []
    for v in available_valets:
        vid = str(v.id)
        active_count = sum(1 for o in all_active_orders if str(o.assigned_valet or '') == vid)
        max_concurrent = v.max_concurrent_orders or global_max
        if active_count < max_concurrent:
            scored.append((active_count, v))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0])
    return scored[0][1]

async def _find_next_available_valet_for_return(return_req, skip_valet_ids: list):
    """
    Find the next best eligible valet for a return pickup.
    - Customer Pincode: Extracted from parent order shipping address.
    - Routing Mode:
      - Delivery Slot Flow: If a slot was specified,
        valet must be available for that slot on the date.
      - Normal Flow (Without Slot Confirmation): If no slot specified,
        any on-duty valet available for today serving customer's pincode is eligible.
    - Capacity: active forward orders + active return pickups < maxConcurrentOrders.
    """
    from datetime import date as dt_date
    from app.db.storage_factory import get_storage
    from app.repositories.product_repository import product_repository
    order_id = return_req.order_id
    order = await order_repository.findById(order_id) if order_id else None
    if not order:
        return None
    shipping_address = order.shipping_address
    customer_pincode = str(shipping_address.pincode) if shipping_address and shipping_address.pincode else ''
    if not customer_pincode:
        user = await user_repository.findById(return_req.user_id) if (return_req.user_id) else None
        if user and user.address:
            customer_pincode = str(user.address.pincode) if user.address and user.address.pincode else ''
    if not customer_pincode:
        return None
    seller_id = return_req.seller_id
    if not seller_id:
        items = (return_req.items) or []
        if items:
            p_id = items[0].product_id
            prod = await product_repository.findById(p_id) if p_id else None
            if prod:
                seller_id = prod.sellers[0].seller_id if prod.sellers else None
        if not seller_id:
            seller_id = order.seller_id
    if seller_id:
        seller = await user_repository.findById(seller_id)
    else:
        seller = await user_repository.findSuperAdmin()
    slot_id = return_req.delivery_slot_id
    slot_date = (return_req.delivery_slot_date) or dt_date.today().isoformat()
    all_valets = await user_repository.findAll(UserFilter(role='valet', is_on_duty=True))
    print(f"DEBUG: all_valets={len(all_valets)}")
    skip_ids: set[str] = set()
    for entry in skip_valet_ids:
        vid = entry
        if vid:
            skip_ids.add(str(vid))
        else:
            skip_ids.add(str(entry))
    eligible_valets = [v for v in all_valets if str(v.id) not in skip_ids]
    print(f"DEBUG: eligible_valets={len(eligible_valets)}")
    if not eligible_valets:
        return None
    from app.repositories.zone_seller_cache import get_zone_for_pincode
    zone = await get_zone_for_pincode(customer_pincode)
    if not zone:
        logger.warning('[ValetTimeout] Return %s: customer pincode %s not in any zone — cannot route', return_req.id, customer_pincode)
        return None
    customer_zone_id = str(zone.id)
    print(f"DEBUG: customer_zone_id={customer_zone_id}")
    availability_storage = get_storage('valetAvailability')
    query_date = slot_date if slot_id else dt_date.today().isoformat()
    availability_records = await availability_storage.findAll(ValetAvailabilityFilter(date=query_date))
    available_valets = []
    for v in eligible_valets:
        vid = str(v.id)
        avail = next((rec for rec in availability_records if str(rec.valet_id) == vid), None)
        if not avail:
            continue
        valet_daily_zones = set(avail.zones or [])
        print(f"DEBUG: checking if {customer_zone_id} in {valet_daily_zones}")
        if customer_zone_id not in valet_daily_zones:
            continue
        if slot_id:
            if avail.availability_type == 'full_day' or (avail.slots and slot_id in avail.slots):
                available_valets.append(v)
        elif avail.availability_type == 'full_day' or (avail.slots and len(avail.slots) > 0):
            available_valets.append(v)
    print(f"DEBUG: available_valets={len(available_valets)}")
    if not available_valets:
        return None
    sys_storage = get_storage('systemSettings')
    sys_settings = await sys_storage.findById(1)
    global_max = (sys_settings.max_concurrent_orders or 1) if sys_settings else 1
    BUSY_STATUSES = ['pending_valet', 'shipped', 'return_pickup']
    ACTIVE_RETURN_STATUSES = ['pending_valet', 'assigned']
    available_valet_ids = [str(v.id) for v in available_valets]
    active_orders = await order_repository.findAll(OrderFilter(statuses=BUSY_STATUSES))
    all_active_orders = [o for o in active_orders if str(o.assigned_valet or '') in available_valet_ids]
    all_active_returns = []
    for st in ACTIVE_RETURN_STATUSES:
        st_returns = await return_request_repository.findAll(status=st)
        all_active_returns.extend([r for r in st_returns if str(r.valet_id or '') in available_valet_ids])
    scored = []
    for v in available_valets:
        vid = str(v.id)
        order_load = sum(1 for o in all_active_orders if str(o.assigned_valet or '') == vid)
        return_load = sum(
            (1 if str(r.valet_id or '') == vid else 0) + (1 if str(r.pending_valet_id or '') == vid else 0)
            for r in all_active_returns
        )
        total_active_load = order_load + return_load
        max_concurrent = v.max_concurrent_orders or global_max
        if total_active_load < max_concurrent:
            scored.append((total_active_load, v))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0])
    return scored[0][1]

async def _cascade_or_revert_return(return_req):
    """
    Cascade return pickup offer to the next best valet or revert to 'pending'
    and notify Super Admin / Seller.
    """
    req_id = return_req.id
    declined_history = list(return_req.valet_decline_history or [])
    next_valet = await _find_next_available_valet_for_return(return_req, declined_history)
    now_iso = datetime.now(timezone.utc).isoformat()
    if next_valet:
        next_valet_id = str(next_valet.id)
        cascade_count = (return_req.valet_cascade_count or 0) + 1
        await return_request_repository.update(req_id, ReturnRequestInternalUpdate(status='pending_valet', pendingValetId=next_valet_id, valetAssignedAt=now_iso, valetCascadeCount=cascade_count, valetDeclineHistory=declined_history))
        try:
            from app.services.push_notification_service import push_notification_service
            return_num = return_req.return_id or req_id
            await push_notification_service.send_to_user(next_valet_id, PushNotificationPayload(title='New Return Pickup Request', message=f'You have a new return pickup request #{return_num}. Please respond within 20 minutes.', link='/valet', data=PushNotificationMetadata(returnId=req_id, type='valet_return_assignment', timeoutMinutes=20)))
        except Exception as e:
            logger.error('[ValetTimeout] Failed to notify next valet for return %s: %s', next_valet_id, e)
        logger.info('[ValetTimeout] Return %s cascaded to valet %s (cascade #%d)', req_id, next_valet_id, cascade_count)
    else:
        await return_request_repository.update(req_id, ReturnRequestInternalUpdate(status='pending', pendingValetId=None, valetAssignedAt=None, valetCascadeCount=(return_req.valet_cascade_count or 0) + 1))
        try:
            from app.services.push_notification_service import push_notification_service
            super_admin = await user_repository.findSuperAdmin()
            return_num = return_req.return_id or req_id
            if super_admin:
                await push_notification_service.send_to_user(str(super_admin.id), PushNotificationPayload(title='Return Valet Unavailable — Reassign Required', message=f'No valets accepted return pickup #{return_num}. Please reassign manually.', link='/admin/returns-management', data=PushNotificationMetadata(returnId=req_id, type='valet_return_all_declined')))
        except Exception as e:
            logger.error('[ValetTimeout] Failed to notify admin for return %s: %s', req_id, e)
        logger.info('[ValetTimeout] Return %s reverted to pending — no valets available', req_id)

async def run_valet_timeout_job():
    """Entry point called by the scheduler every 1 minute for both forward orders and returns."""
    try:
        pending_orders = await order_repository.findAll(OrderFilter(status='pending_valet'))
        now = datetime.now(timezone.utc)
        if pending_orders:
            for order in pending_orders:
                assigned_at = order.valet_assigned_at
                if not assigned_at:
                    continue
                try:
                    if isinstance(assigned_at, str):
                        assigned_at = datetime.fromisoformat(assigned_at.replace('Z', '+00:00'))
                    if assigned_at.tzinfo is None:
                        assigned_at = assigned_at.replace(tzinfo=timezone.utc)
                except (ValueError, AttributeError):
                    continue
                is_urgent = order.is_urgent_delivery
                timeout_minutes = URGENT_TIMEOUT_MINUTES if is_urgent else NORMAL_TIMEOUT_MINUTES
                deadline = assigned_at + timedelta(minutes=timeout_minutes)
                if now >= deadline:
                    pending_valet_id = order.pending_valet_id
                    if pending_valet_id:
                        history = list(order.valet_decline_history or [])
                        if not any(d.valet_id == pending_valet_id for d in history):
                            from app.models.schemas import ValetDeclineHistoryEntry
                            history.append(ValetDeclineHistoryEntry(valetId=pending_valet_id, reason='timeout'))
                        order.valet_decline_history = history
                        await order_repository.update(str(order.id), OrderInternalUpdate(valetDeclineHistory=history, pendingValetId=None))
                        order = await order_repository.findById(str(order.id))
                    await _cascade_or_revert(order)
        pending_returns = await return_request_repository.findAll(status='pending_valet')
        if pending_returns:
            for ret in pending_returns:
                assigned_at = ret.valet_assigned_at
                if not assigned_at:
                    continue
                try:
                    if isinstance(assigned_at, str):
                        assigned_at = datetime.fromisoformat(assigned_at.replace('Z', '+00:00'))
                    if assigned_at.tzinfo is None:
                        assigned_at = assigned_at.replace(tzinfo=timezone.utc)
                except (ValueError, AttributeError):
                    continue
                deadline = assigned_at + timedelta(minutes=NORMAL_TIMEOUT_MINUTES)
                if now >= deadline:
                    req_id = ret.id
                    pending_valet_id = ret.pending_valet_id
                    if pending_valet_id:
                        history = list(ret.valet_decline_history or [])
                        if not any(d.valet_id == pending_valet_id for d in history):
                            from app.models.daos_flat import ReturnRequestValetDeclineInternal
                            history.append(ReturnRequestValetDeclineInternal(valet_id=pending_valet_id, reason='timeout'))
                        ret.valet_decline_history = history
                        await return_request_repository.update(req_id, ReturnRequestInternalUpdate(valetDeclineHistory=history, pendingValetId=None))
                        ret = await return_request_repository.findById(req_id)
                    await _cascade_or_revert_return(ret)
    except Exception as e:
        logger.error('[ValetTimeout] Unexpected error in timeout job: %s', e, exc_info=True)