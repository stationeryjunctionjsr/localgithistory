import asyncio
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.base import CamelBaseModel
from app.models.schemas import AnalyticsEventCreate
from app.utils.logger import logger
from app.db.storage_factory import get_storage
from app.repositories.tracking_repository import tracking_repository

class RawEventPayload(CamelBaseModel):
    returning: Optional[bool] = False
    product_id: Optional[str] = None
    product_name: Optional[str] = "Unknown"
    source: Optional[str] = "mobile_app"
    quantity: Optional[int] = 1
    query: Optional[str] = ""
    results_count: Optional[int] = 0
    reason: Optional[str] = "unknown"

class RawEvent(CamelBaseModel):
    type: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: Optional[str] = None
    payload: RawEventPayload = Field(default_factory=RawEventPayload)
    page: Optional[str] = "/"

async def run_events_sync_job_async():
    logger.info("Starting daily events synchronization job...")
    try:
        events_store = get_storage("events")
        tracking_store = get_storage("tracking")

        events = await events_store.findAll()
        existing_tracking = await tracking_store.findAll()
        existing_keys = {(t.type, t.session_id, t.timestamp) for t in existing_tracking}

        migrated_count = 0
        for e in events:
            event_type = e.eventType
            session_id = None
            user_id = None
            timestamp = e.created_at.isoformat() if e.created_at else None
            payload = RawEventPayload()
            for item in (e.payload or []):
                if item.key == "sessionId":
                    session_id = item.value
                elif item.key == "userId":
                    user_id = item.value
                elif item.key == "timestamp":
                    timestamp = item.value
                elif item.key == "returning":
                    payload.returning = str(item.value).lower() in ("true", "1")
                elif item.key == "productId":
                    payload.product_id = item.value
                elif item.key == "productName":
                    payload.product_name = item.value
                elif item.key == "source":
                    payload.source = item.value
                elif item.key == "quantity":
                    payload.quantity = int(item.value) if item.value is not None else 1
                elif item.key == "query":
                    payload.query = item.value
                elif item.key == "resultsCount":
                    payload.results_count = int(item.value) if item.value is not None else 0
                elif item.key == "reason":
                    payload.reason = item.value

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

            # Build typed tracking event model
            doc = AnalyticsEventCreate(
                type=tracking_type,
                user_id=user_id,
                session_id=session_id,
                timestamp=timestamp,
            )

            if event_type == "session_start":
                doc.is_returning = payload.returning
                doc.page_views = 1
            elif event_type == "page_view":
                doc.page = e.page
            elif event_type == "product_view":
                doc.product_id = payload.product_id
                doc.product_name = payload.product_name
            elif event_type == "product_click":
                doc.product_id = payload.product_id
                doc.product_name = payload.product_name
                doc.source = payload.source
            elif event_type == "add_to_cart":
                doc.product_id = payload.product_id
                doc.quantity = payload.quantity
            elif event_type == "remove_from_cart":
                doc.product_id = payload.product_id
                doc.quantity = payload.quantity
            elif event_type == "search":
                doc.search_term = payload.query
                doc.results_count = payload.results_count
                doc.segment = "customer"
            elif event_type == "add_to_wishlist":
                doc.product_id = payload.product_id
            elif event_type == "begin_checkout":
                doc.page = "/checkout/step1"
            elif event_type == "purchase":
                doc.page = "/checkout/complete"
            elif event_type == "session_end":
                doc.reason = payload.reason

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
