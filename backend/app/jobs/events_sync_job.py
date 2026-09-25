import asyncio
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from app.utils.logger import logger
from app.db.storage_factory import get_storage
from app.repositories.tracking_repository import tracking_repository

class RawEventPayload(BaseModel):
    returning: Optional[bool] = False
    productId: Optional[str] = None
    productName: Optional[str] = "Unknown"
    source: Optional[str] = "mobile_app"
    quantity: Optional[int] = 1
    query: Optional[str] = ""
    resultsCount: Optional[int] = 0
    reason: Optional[str] = "unknown"

class RawEvent(BaseModel):
    type: Optional[str] = None
    sessionId: Optional[str] = None
    userId: Optional[str] = None
    timestamp: Optional[str] = None
    payload: RawEventPayload = Field(default_factory=RawEventPayload)
    page: Optional[str] = "/"

class TrackingEventDoc(BaseModel):
    type: Optional[str] = None
    sessionId: Optional[str] = None
    timestamp: Optional[str] = None

async def run_events_sync_job_async():
    logger.info("Starting daily events synchronization job...")
    try:
        events_store = get_storage("events")
        tracking_store = get_storage("tracking")

        events = await events_store.findAll()
        existing_tracking = await tracking_store.findAll()
        existing_keys = set()
        
        for t_dict in existing_tracking:
            t = TrackingEventDoc.model_validate(t_dict)
            existing_keys.add((t.type, t.session_id, t.timestamp))

        migrated_count = 0
        for e in events:
            event_type = e.eventType
            session_id = None
            user_id = None
            timestamp = e.createdAt.isoformat() if e.createdAt else None
            payload_dict = {}
            for item in (e.payload or []):
                if item.key == 'sessionId': session_id = item.value
                elif item.key == 'userId': user_id = item.value
                elif item.key == 'timestamp': timestamp = item.value
                else: payload_dict[item.key] = item.value
            
            # Use RawEventPayload constructor explicitly
            payload = RawEventPayload(**payload_dict)

            # Translate event_type to tracking type
            tracking_type = None
            if event_type == "session_start":
                tracking_type = "session"
            elif event_type == "page_view":
                tracking_type = "page_view"
            elif event_type == "product_view":
                tracking_type = "product_view"
            elif event_type == "product_click":
                tracking_type = "product_click"
            elif event_type == "add_to_cart":
                tracking_type = "cart_add"
            elif event_type == "remove_from_cart":
                tracking_type = "cart_item_remove"
            elif event_type == "search":
                tracking_type = "product_search"
            elif event_type == "add_to_wishlist":
                tracking_type = "wishlist_add"
            elif event_type in ["begin_checkout", "purchase"]:
                tracking_type = "page_view"
            elif event_type == "session_end":
                tracking_type = "session_end"

            if not tracking_type:
                continue

            key = (tracking_type, session_id, timestamp)
            if key in existing_keys:
                continue

            # Build tracking document
            doc = {
                "type": tracking_type,
                "userId": user_id,
                "sessionId": session_id,
                "timestamp": timestamp,
            }

            if event_type == "session_start":
                doc["isReturning"] = payload.returning
                doc["pageViews"] = 1
            elif event_type == "page_view":
                doc["page"] = e.page
            elif event_type == "product_view":
                doc["productId"] = payload.product_id
                doc["productName"] = payload.product_name
            elif event_type == "product_click":
                doc["productId"] = payload.product_id
                doc["productName"] = payload.product_name
                doc["source"] = payload.source
            elif event_type == "add_to_cart":
                doc["productId"] = payload.product_id
                doc["quantity"] = payload.quantity
            elif event_type == "remove_from_cart":
                doc["productId"] = payload.product_id
                doc["quantity"] = payload.quantity
            elif event_type == "search":
                doc["searchTerm"] = payload.query
                doc["resultsCount"] = payload.results_count
                doc["segment"] = "customer"
            elif event_type == "add_to_wishlist":
                doc["productId"] = payload.product_id
            elif event_type == "begin_checkout":
                doc["page"] = "/checkout/step1"
            elif event_type == "purchase":
                doc["page"] = "/checkout/complete"
            elif event_type == "session_end":
                doc["reason"] = payload.reason

            await tracking_repository.create(doc)
            migrated_count += 1

        logger.info("Daily events synchronization job finished. Synced %d events.", migrated_count)
    except Exception as exc:
        logger.error("Error in run_events_sync_job_async: %s", str(exc), exc_info=True)


def run_events_sync_job():
    """
    Sync job runner called from the AP scheduler.
    Since scheduler executes in a thread pool, we run the async loop here.
    """
    try:
        asyncio.run(run_events_sync_job_async())
    except Exception as exc:
        logger.error("Error in run_events_sync_job: %s", str(exc), exc_info=True)


if __name__ == "__main__":
    run_events_sync_job()
