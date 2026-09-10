import asyncio
from app.db.mysql_order_dao import MySQLOrderDAO

async def main():
    dao = MySQLOrderDAO()
    # 1. Create a dummy order
    data = {
        "user": 1,
        "orderNumber": "TEST-1234",
        "status": "pending_valet",
        "pendingValetId": "v123",
        "valetAssignedAt": "2026-09-10T12:00:00Z",
        "valetCascadeCount": 1,
        "isUrgentDelivery": True,
        "valetDeclineHistory": [{"valetId": "v111", "reason": "timeout"}],
        "items": []
    }
    
    print("Creating order...")
    new_doc = await dao.create(data)
    oid = new_doc["_id"]
    print("Created order:", oid)
    print("pendingValetId:", new_doc.get("pendingValetId"))
    print("valetCascadeCount:", new_doc.get("valetCascadeCount"))
    print("valetDeclineHistory:", new_doc.get("valetDeclineHistory"))
    print("isUrgentDelivery:", new_doc.get("isUrgentDelivery"))
    
    # 2. Update the order
    print("\nUpdating order...")
    update_data = {
        "pendingValetId": "v999",
        "valetCascadeCount": 2,
        "valetDeclineHistory": [{"valetId": "v111", "reason": "timeout"}, {"valetId": "v123", "reason": "timeout"}],
        "isUrgentDelivery": False
    }
    updated_doc = await dao.update(oid, update_data)
    print("Updated pendingValetId:", updated_doc.get("pendingValetId"))
    print("Updated valetCascadeCount:", updated_doc.get("valetCascadeCount"))
    print("Updated valetDeclineHistory:", updated_doc.get("valetDeclineHistory"))
    print("Updated isUrgentDelivery:", updated_doc.get("isUrgentDelivery"))
    
    # 3. Clean up
    await dao.delete(oid)
    print("\nCleaned up test order.")

asyncio.run(main())
