import asyncio
from app.db.mysql_deliveryCharges_dao import MySQLDeliveryChargesDAO
from app.models.daos_flat import DeliveryChargeInternalCreate

async def main():
    try:
        dao = MySQLDeliveryChargesDAO()
        charge = DeliveryChargeInternalCreate(
            pincode="123456",
            state="State",
            city="City",
            district="District",
            serviceableForCustomer=True,
            serviceableForWholesaler=True,
            charge=0.0,
            isActive=True,
            applyDefaultCharge=False
        )
        await dao.create(charge)
        print("Inserted pincode 123456")
    except Exception as e:
        print(f"Failed to insert: {e}")

asyncio.run(main())
