
import asyncio
from app.repositories.coupon_repository import coupon_repository

async def debug():
    docs = await coupon_repository.storage.findAll({})
    print("Found total:", len(docs))
    for doc in docs:
        if "SKU-TEST-COUPON-MODE" in str(doc):
            print("Found match:", doc)
        if doc.get("method") == "automatic":
            print("Found automatic:", doc)

asyncio.run(debug())

