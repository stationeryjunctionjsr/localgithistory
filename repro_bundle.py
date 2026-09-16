import asyncio
from app.repositories.bundle_repository import bundle_repository
from app.models.daos import BundleInternalCreate
data = {
            "name": "High Volume Bundle",
            "price": 45.0,
            "isActive": True,
            "products": [{"productId": "pid1", "quantity": 2}],
            "salesCount": 20,
        }
async def main():
    try:
        b = await bundle_repository.create(data)
        print("Success:", getattr(b, "id", "No ID"))
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
