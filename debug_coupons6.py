
import asyncio
from app.repositories.coupon_repository import coupon_repository

async def debug():
    docs = await coupon_repository.get_active_automatic_product_discounts()
    print("Found active:", len(docs))
    for doc in docs:
        print(doc)

asyncio.run(debug())

