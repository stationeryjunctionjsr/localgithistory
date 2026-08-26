import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.storage_factory import get_storage
from app.repositories.seller_request_repository import seller_request_repository


async def main():
    store = get_storage("sellerRequests")
    print(f"Store type: {type(store)}")

    # create
    req = await seller_request_repository.create(
        {
            "user": "test_user",
            "subject": "test_subj",
            "description": "test_desc",
        }
    )
    print("Created:", req)

    # get
    req2 = await seller_request_repository.findById(req["_id"])
    print("Fetched:", req2)

    # add response
    req3 = await seller_request_repository.addResponse(
        req["_id"], {"user": "admin_user", "message": "hello", "isAdminResponse": True}
    )
    print("With Response:", req3)


asyncio.run(main())
