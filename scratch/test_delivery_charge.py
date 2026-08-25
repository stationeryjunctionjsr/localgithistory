import asyncio
import os
import sys

# Add backend app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.repositories.delivery_charge_repository import delivery_charge_repository


async def main():
    # Let's see what getChargeForLocation returns
    # We will pass dummy location values
    res = await delivery_charge_repository.getChargeForLocation(
        state="Jharkhand",
        city="Jamshedpur",
        district="East Singhbhum",
        pincode="831001",
        user_role="customer",
        order_amount=500,
    )
    print("Result:", res)


if __name__ == "__main__":
    asyncio.run(main())
