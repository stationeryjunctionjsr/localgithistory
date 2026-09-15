import secrets
from datetime import datetime, timezone
from typing import Dict, Optional, Any

from app.db.storage_factory import get_storage
from app.models.daos import SellerRequestInternalCreate, SellerRequestInternalUpdate


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
        if "category" in query and "category" not in storage_query:
            requests = [r for r in requests if r.category == query["category"]]
        if "subject" in query and "subject" not in storage_query:
            requests = [r for r in requests if r.subject == query["subject"]]
        if "requestNumber" in query and "requestNumber" not in storage_query:
            requests = [r for r in requests if r.requestNumber == query["requestNumber"]]

        # Sort by creation date (newest first)
        requests.sort(key=lambda x: x.createdAt if x.createdAt else "", reverse=True)

        return requests

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, request_data: SellerRequestInternalCreate):
        request_data.requestNumber = self.generateRequestNumber()
        request_data.createdAt = datetime.now(timezone.utc).isoformat()
        if request_data.category is None:
            request_data.category = "general"
        if request_data.priority is None:
            request_data.priority = "medium"
        if request_data.status is None:
            request_data.status = "open"
        if request_data.attachments is None:
            request_data.attachments = []
        if request_data.responses is None:
            request_data.responses = []
            
        return await self.storage.create(request_data)

    async def update(self, id: str, update_data: SellerRequestInternalUpdate):
        if update_data.status == "resolved" and update_data.resolvedAt is None:
            update_data.resolvedAt = datetime.now(timezone.utc).isoformat()
        elif update_data.status == "closed" and update_data.closedAt is None:
            update_data.closedAt = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

    async def addResponse(self, request_id: str, response_data: Any):
        request = await self.findById(request_id)
        if not request:
            raise ValueError("Request not found")

        response = {
            "user": response_data.user,
            "message": response_data.message,
            "attachments": response_data.attachments if response_data.attachments is not None else [],
            "isAdminResponse": response_data.isAdminResponse if response_data.isAdminResponse is not None else False,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        if request.responses is None:
            request.responses = []
        request.responses.append(response)

        # Update request status if admin responds
        if response_data.isAdminResponse and request.status == "open":
            request.status = "in_progress"

        update_payload = SellerRequestInternalUpdate(
            responses=request.responses,
            status=request.status
        )

        return await self.update(request_id, update_payload)

    async def delete(self, id: str):
        return await self.storage.delete(id)


seller_request_repository = SellerRequestRepository()
