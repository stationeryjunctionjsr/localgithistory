from datetime import datetime
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage


class ReturnRequestRepository:
    def __init__(self):
        self.storage = get_storage("returnRequests")

    async def generateReturnId(self) -> str:
        prefix = "RET-"
        all_requests = await self.storage.findAll()
        max_id = 0
        import re

        for req in all_requests:
            match = re.match(f"{re.escape(prefix)}(\\d+)", req.get("id", ""))
            if match:
                max_id = max(max_id, int(match.group(1)))
        next_id = max(1, max_id + 1)
        return f"{prefix}{next_id}"

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        requests = await self.storage.findAll()
        if query:
            filtered = []
            for req in requests:
                match = True
                for k, v in query.items():
                    if req.get(k) != v:
                        match = False
                        break
                if match:
                    filtered.append(req)
            requests = filtered

        # Sort by creation date (newest first)
        requests.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        return requests

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def findByOrderId(self, order_id: str) -> List[Dict]:
        return await self.findAll({"orderId": order_id})

    async def create(self, data: Dict) -> Dict:
        return_id = await self.generateReturnId()
        request = {
            "id": return_id,
            "orderId": data["orderId"],
            "userId": data["userId"],
            "items": data["items"],
            "paymentMethod": data["paymentMethod"],
            "upiPaymentScreenshot": data.get("upiPaymentScreenshot"),
            "notes": data.get("notes"),
            "status": data.get("status", "pending"),
            "valetId": data.get("valetId"),
            "deliveryCharge": data.get("deliveryCharge", 0),
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        }
        return await self.storage.create(request)

    async def update(self, id: str, update_data: Dict) -> Dict:
        update_data["updatedAt"] = datetime.utcnow().isoformat()
        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> Dict:
        return await self.storage.delete(id)


return_request_repository = ReturnRequestRepository()
