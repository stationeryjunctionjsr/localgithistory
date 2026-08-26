import asyncio
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.database import get_async_session_factory
from sqlalchemy import text


async def run_backfill():
    factory = get_async_session_factory()
    if not factory:
        print("Could not get database session factory.")
        return

    print("Starting product sellers backfill...")
    count = 0

    async with factory() as session:
        result = await session.execute(text("SELECT external_id, details FROM sj_products WHERE details IS NOT NULL"))
        products = result.fetchall()

        insert_sql = text("""
            INSERT IGNORE INTO sj_product_sellers
            (product_id, seller_id, is_active, request_status, stock)
            VALUES (:product_id, :seller_id, :is_active, :request_status, :stock)
        """)

        for p in products:
            try:
                details_json = p.details
                if isinstance(details_json, str):
                    details = json.loads(details_json)
                else:
                    details = details_json

                sellers = details.get("sellers", [])
                if not isinstance(sellers, list):
                    continue

                for s in sellers:
                    if not isinstance(s, dict):
                        continue

                    seller_id = str(s.get("sellerId", ""))
                    if not seller_id or seller_id == "null":
                        continue

                    is_active_val = s.get("isActive")
                    is_active = 1 if (str(is_active_val).lower() == "true" or is_active_val is True) else 0

                    req_status = s.get("requestStatus") or "approved"

                    stock_val = s.get("stock", 0)
                    try:
                        stock = int(stock_val)
                    except:
                        stock = 0

                    await session.execute(
                        insert_sql,
                        {
                            "product_id": p.external_id,
                            "seller_id": seller_id,
                            "is_active": is_active,
                            "request_status": req_status,
                            "stock": stock,
                        },
                    )
                    count += 1
            except Exception as e:
                print(f"Error processing product {p.external_id}: {e}")

        await session.commit()
        print(f"Successfully backfilled {count} seller records into sj_product_sellers.")


if __name__ == "__main__":
    asyncio.run(run_backfill())
