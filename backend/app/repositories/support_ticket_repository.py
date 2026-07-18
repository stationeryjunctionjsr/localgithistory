import secrets
from datetime import datetime
from typing import Dict, Optional

from app.db.storage_factory import get_storage


class SupportTicketRepository:
    def __init__(self):
        self.storage = get_storage("supportTickets")

    def generateTicketNumber(self) -> str:
        return f"TKT-{int(datetime.utcnow().timestamp() * 1000)}-{secrets.token_hex(4).upper()}"

    async def findAll(self, query: Optional[Dict] = None):
        tickets = await self.storage.findAll()

        query = query or {}

        if query.get("user"):
            tickets = [t for t in tickets if t.get("user") == query["user"]]

        if query.get("status"):
            tickets = [t for t in tickets if t.get("status") == query["status"]]

        if query.get("priority"):
            tickets = [t for t in tickets if t.get("priority") == query["priority"]]

        # Sort by creation date (newest first)
        tickets.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        return tickets

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, ticket_data: Dict):
        ticket = {
            "ticketNumber": self.generateTicketNumber(),
            "user": ticket_data.get("user"),
            "name": ticket_data.get("name"),
            "email": ticket_data.get("email"),
            "phone": ticket_data.get("phone"),
            "company": ticket_data.get("company"),
            "subject": ticket_data["subject"],
            "description": ticket_data["description"],
            "category": ticket_data.get("category", "general"),
            "priority": ticket_data.get("priority", "medium"),
            "status": ticket_data.get("status", "open"),
            "attachments": ticket_data.get("attachments", []),
            "assignedTo": ticket_data.get("assignedTo"),
            "responses": [],
            "resolvedAt": None,
            "closedAt": None,
            "createdAt": datetime.utcnow().isoformat(),
        }

        return await self.storage.create(ticket)

    async def update(self, id: str, update_data: Dict):
        if update_data.get("status") == "resolved" and "resolvedAt" not in update_data:
            update_data["resolvedAt"] = datetime.utcnow().isoformat()
        elif update_data.get("status") == "closed" and "closedAt" not in update_data:
            update_data["closedAt"] = datetime.utcnow().isoformat()

        return await self.storage.update(id, update_data)

    async def addResponse(self, ticket_id: str, response_data: Dict):
        ticket = await self.findById(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        response = {
            "user": response_data["user"],
            "message": response_data["message"],
            "attachments": response_data.get("attachments", []),
            "isAdminResponse": response_data.get("isAdminResponse", False),
            "createdAt": datetime.utcnow().isoformat(),
        }

        ticket["responses"] = ticket.get("responses", [])
        ticket["responses"].append(response)

        # Update ticket status if admin responds
        if response_data.get("isAdminResponse") and ticket.get("status") == "open":
            ticket["status"] = "in_progress"

        return await self.update(ticket_id, {"responses": ticket["responses"], "status": ticket["status"]})

    async def delete(self, id: str):
        return await self.storage.delete(id)


support_ticket_repository = SupportTicketRepository()
