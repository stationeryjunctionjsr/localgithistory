import re

with open('app/routers/analytics.py', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to extract device object correctly before dumping it as JSON, or instead of dumping it as JSON, explode it.
# Actually, the user asked to break it up, so let's parse it and add it as Flat properties if it's a dict!

device_extraction = '''
    if getattr(event, "device", None):
        val = event.device
        if isinstance(val, dict):
            if val.get("type"):
                payload_items.append(EventPayloadItem(key="device_type", value=str(val["type"])))
            if val.get("os"):
                payload_items.append(EventPayloadItem(key="device_os", value=str(val["os"])))
            if val.get("osVersion"):
                payload_items.append(EventPayloadItem(key="device_os_version", value=str(val["osVersion"])))
            if val.get("model"):
                payload_items.append(EventPayloadItem(key="device_model", value=str(val["model"])))
            if val.get("appVersion"):
                payload_items.append(EventPayloadItem(key="device_app_version", value=str(val["appVersion"])))
            if val.get("browser"):
                payload_items.append(EventPayloadItem(key="device_browser", value=str(val["browser"])))
        else:
            payload_items.append(EventPayloadItem(key="device_model", value=str(val)))
'''

# Find the old device block and replace it
text = re.sub(r'    if getattr\(event, "device", None\):.*?payload_items\.append\(EventPayloadItem\(key="device", value=val\)\)', device_extraction, text, flags=re.DOTALL)

# Now reverse the dual-write flow!
# The router currently does:
# stored = await analytics_repository.record_event(event_create)
# then track things.

sync_logic = '''
        event_type = event.type
        session_id = event.sessionId
        raw_payload = event.payload
        payload_obj = raw_payload or AnalyticsEventPayload()
        tracking_obj = None

        try:
            if event_type == "session_start":
                is_returning = bool(payload_obj.returning) if payload_obj.returning is not None else False
                tracking_obj = await tracking_repository.trackSession(user_id, session_id, is_returning)
            elif event_type == "page_view":
                page = event.page if event.page is not None else "/"
                tracking_obj = await tracking_repository.trackPageView(user_id, page, session_id)
            elif event_type == "product_view":
                product_id = payload_obj.productId
                product_name = payload_obj.productName if payload_obj.productName is not None else "Unknown"
                if product_id:
                    tracking_obj = await tracking_repository.trackProductView(user_id, product_id, product_name, session_id)
            elif event_type == "product_click":
                product_id = payload_obj.productId
                product_name = payload_obj.productName if payload_obj.productName is not None else "Unknown"
                source = payload_obj.source if payload_obj.source is not None else "mobile_app"
                if product_id:
                    tracking_obj = await tracking_repository.trackProductClick(user_id, product_id, product_name, source, session_id)
            elif event_type == "add_to_cart":
                product_id = payload_obj.productId
                quantity = payload_obj.quantity if payload_obj.quantity is not None else 1
                if product_id:
                    tracking_obj = await tracking_repository.trackCartAdd(user_id, product_id, quantity, session_id)
            elif event_type == "remove_from_cart":
                product_id = payload_obj.productId
                quantity = payload_obj.quantity if payload_obj.quantity is not None else 1
                if product_id:
                    tracking_obj = await tracking_repository.trackCartItemRemove(user_id, product_id, quantity, session_id)
            elif event_type == "search":
                query = payload_obj.query if payload_obj.query is not None else ""
                results_count = payload_obj.resultsCount if payload_obj.resultsCount is not None else 0
                tracking_obj = await tracking_repository.trackSearch(user_id, query, results_count, session_id, segment="customer")
            elif event_type == "add_to_wishlist":
                product_id = payload_obj.productId
                if product_id:
                    tracking_obj = await tracking_repository.trackWishlistAdd(user_id, product_id, "Unknown", session_id)
            elif event_type == "session_end":
                reason = payload_obj.reason if payload_obj.reason is not None else "unknown"
                from app.models.schemas import AnalyticsEventCreate
                tracking_obj = await tracking_repository.create(
                    AnalyticsEventCreate(type="session_end", userId=user_id, sessionId=session_id, reason=reason)
                )
            elif event_type == "begin_checkout":
                tracking_obj = await tracking_repository.trackPageView(user_id, "/checkout/step1", session_id)
            elif event_type == "purchase":
                tracking_obj = await tracking_repository.trackPageView(user_id, "/checkout/complete", session_id)
        except Exception as sync_err:
            logger.error("Failed to sync event to tracking repository: %s", str(sync_err), exc_info=True)

        if tracking_obj:
            event_create.tracking_id = int(tracking_obj.id)
            
        stored = await analytics_repository.record_event(event_create)
'''

# Find the block where event_create is defined, up to stored = await analytics_repository.record_event(event_create)
# and the whole tracking block, and replace it.

text = re.sub(r'    try:\n        stored = await analytics_repository.record_event\(event_create\)\n\n        # Sync/replicate mobile events to tracking repository.*logger\.error\("Failed to sync event to tracking repository: %s", str\(sync_err\), exc_info=True\)', sync_logic, text, flags=re.DOTALL)

with open('app/routers/analytics.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated router dual-write order and exploded device")
