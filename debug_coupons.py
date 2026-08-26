
import asyncio
from app.repositories.coupon_repository import coupon_repository

async def debug():
    docs = await coupon_repository.storage.findAll({"method": "automatic"})
    for doc in docs:
        print(doc.get("code"), doc.get("method"), doc.get("typeOfDiscount"))

asyncio.run(debug())

