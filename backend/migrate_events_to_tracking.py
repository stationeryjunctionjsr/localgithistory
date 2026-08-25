import asyncio
import os
import sys

# Add backend root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.storage_factory import get_storage
from app.repositories.tracking_repository import tracking_repository


async def migrate():
    print("Starting event migration...")
    events_store = get_storage("events")
    tracking_store = get_storage("tracking")

    events = await events_store.findAll()
    print(f"Found {len(events)} events in events collection/file.")

    # Get existing tracking records to avoid duplication
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

        # Create record in tracking collection
        await tracking_repository.create(doc)
        migrated_count += 1

    print(f"Migration completed! Migrated {migrated_count} events to tracking repository.")


if __name__ == "__main__":
    asyncio.run(migrate())
