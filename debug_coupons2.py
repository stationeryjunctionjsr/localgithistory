
import asyncio
from app.repositories.coupon_repository import coupon_repository

async def debug():
    docs = await coupon_repository.storage.findAll(
        {"method": "automatic", "isActive": True, "typeOfDiscount": "product_discount"}
    )
    print("Found:", len(docs))
    for doc in docs:
        print(doc)

asyncio.run(debug())

