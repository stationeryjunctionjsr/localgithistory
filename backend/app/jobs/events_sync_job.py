import asyncio
from datetime import datetime
from app.utils.logger import logger
from app.db.storage_factory import get_storage
from app.repositories.tracking_repository import tracking_repository

async def run_events_sync_job_async():
    logger.info("Starting daily events synchronization job...")
    try:
        events_store = get_storage("events")
        tracking_store = get_storage("tracking")
        
        events = await events_store.findAll()
        existing_tracking = await tracking_store.findAll()
        existing_keys = set()
        for t in existing_tracking:
            existing_keys.add((t.get("type"), t.get("sessionId"), t.get("timestamp")))
            
        migrated_count = 0
        for e in events:
            event_type = e.get("type")
            session_id = e.get("sessionId")
            user_id = e.get("userId")
            timestamp = e.get("timestamp")
            payload = e.get("payload") or {}
            
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
                doc["isReturning"] = payload.get("returning", False)
                doc["pageViews"] = 1
            elif event_type == "page_view":
                doc["page"] = e.get("page", "/")
            elif event_type == "product_view":
                doc["productId"] = payload.get("productId")
                doc["productName"] = payload.get("productName", "Unknown")
            elif event_type == "product_click":
                doc["productId"] = payload.get("productId")
                doc["productName"] = payload.get("productName", "Unknown")
                doc["source"] = payload.get("source", "mobile_app")
            elif event_type == "add_to_cart":
                doc["productId"] = payload.get("productId")
                doc["quantity"] = payload.get("quantity", 1)
            elif event_type == "remove_from_cart":
                doc["productId"] = payload.get("productId")
                doc["quantity"] = payload.get("quantity", 1)
            elif event_type == "search":
                doc["searchTerm"] = payload.get("query", "")
                doc["resultsCount"] = payload.get("resultsCount", 0)
                doc["segment"] = "customer"
            elif event_type == "add_to_wishlist":
                doc["productId"] = payload.get("productId")
            elif event_type == "begin_checkout":
                doc["page"] = "/checkout/step1"
            elif event_type == "purchase":
                doc["page"] = "/checkout/complete"
            elif event_type == "session_end":
                doc["reason"] = payload.get("reason", "unknown")
                
            await tracking_repository.create(doc)
            migrated_count += 1
            
        logger.info("Daily events synchronization job finished. Synced %d events.", migrated_count)
    except Exception as e:
        logger.error("Error in run_events_sync_job_async: %s", str(e), exc_info=True)

def run_events_sync_job():
    """
    Sync job runner called from the AP scheduler.
    Since scheduler executes in a thread pool, we run the async loop here.
    """
    try:
        asyncio.run(run_events_sync_job_async())
    except Exception as e:
        logger.error("Error in run_events_sync_job: %s", str(e), exc_info=True)

if __name__ == "__main__":
    run_events_sync_job()
