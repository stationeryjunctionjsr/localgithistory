import secrets
from datetime import datetime, timezone
from typing import Dict, Optional

from app.db.storage_factory import get_storage


class SellerRequestRepository:
    def __init__(self):
        self.storage = get_storage("sellerRequests")

    def generateRequestNumber(self) -> str:
        return f"SRQ-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{secrets.token_hex(4).upper()}"

    async def findAll(self, query: Optional[Dict] = None):
        query = query or {}
        # Push supported filters to storage to avoid a full-table scan.
        storage_query = {k: v for k, v in query.items() if k in ("user", "status", "priority")}
        requests = await self.storage.findAll(storage_query or None)

        # Python-side filter for any remaining keys not yet pushed to storage
        remaining = {k: v for k, v in query.items() if k not in storage_query}
        for key, val in remaining.items():
            requests = [r for r in requests if r.get(key) == val]

        # Sort by creation date (newest first)
        requests.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        return requests

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, request_data: Any):
        from app.models.daos import SellerRequestInternalCreate
        req_data = request_data if isinstance(request_data, dict) else dict(request_data)
        request = {
            "requestNumber": self.generateRequestNumber(),
            "user": req_data.get("user"),
            "subject": req_data["subject"],
            "description": req_data["description"],
            "category": req_data.get("category", "general"),
            "priority": req_data.get("priority", "medium"),
            "status": req_data.get("status", "open"),
            "attachments": req_data.get("attachments", []),
            "responses": [],
            "resolvedAt": None,
            "closedAt": None,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        return await self.storage.create(SellerRequestInternalCreate(**request))

    async def update(self, id: str, update_data: Any):
        from app.models.daos import SellerRequestInternalUpdate
        update_data_dict = update_data if isinstance(update_data, dict) else dict(update_data)
        if update_data_dict.get("status") == "resolved" and "resolvedAt" not in update_data_dict:
            update_data_dict["resolvedAt"] = datetime.now(timezone.utc).isoformat()
        elif update_data_dict.get("status") == "closed" and "closedAt" not in update_data_dict:
            update_data_dict["closedAt"] = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, SellerRequestInternalUpdate(**update_data_dict))

    async def addResponse(self, request_id: str, response_data: Any):
        request = await self.findById(request_id)
        if not request:
            raise ValueError("Request not found")

        response = {
            "user": response_data["user"],
            "message": response_data["message"],
            "attachments": response_data.get("attachments", []),
            "isAdminResponse": response_data.get("isAdminResponse", False),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        request["responses"] = request.get("responses", [])
        request["responses"].append(response)

        # Update request status if admin responds
        if response_data.get("isAdminResponse") and request.get("status") == "open":
            request["status"] = "in_progress"

        return await self.update(request_id, {"responses": request["responses"], "status": request["status"]})

    async def delete(self, id: str):
        return await self.storage.delete(id)


seller_request_repository = SellerRequestRepository()
