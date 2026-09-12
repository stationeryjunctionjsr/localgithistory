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
        request = {
            "requestNumber": self.generateRequestNumber(),
            "user": request_data.get("user"),
            "subject": request_data["subject"],
            "description": request_data["description"],
            "category": request_data.get("category", "general"),
            "priority": request_data.get("priority", "medium"),
            "status": request_data.get("status", "open"),
            "attachments": request_data.get("attachments", []),
            "responses": [],
            "resolvedAt": None,
            "closedAt": None,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        return await self.storage.create(request)

    async def update(self, id: str, update_data: Any):
        if getattr(update_data, "status", None) == "resolved" and "resolvedAt" not in update_data:
            update_data.resolvedAt = datetime.now(timezone.utc).isoformat()
        elif getattr(update_data, "status", None) == "closed" and "closedAt" not in update_data:
            update_data.closedAt = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

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
