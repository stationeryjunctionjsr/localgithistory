import secrets
from datetime import datetime, timezone
from typing import Dict, Optional

from app.db.storage_factory import get_storage


class SupportTicketRepository:
    def __init__(self):
        self.storage = get_storage("supportTickets")

    def generateTicketNumber(self) -> str:
        return f"TKT-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{secrets.token_hex(4).upper()}"

    async def findAll(self, query: Optional[Dict] = None):
        tickets = await self.storage.findAll()

        query = query or {}

        if query.get("user"):
            tickets = [t for t in tickets if getattr(t, "user", None) == query["user"]]

        if query.get("status"):
            tickets = [t for t in tickets if getattr(t, "status", None) == query["status"]]

        if query.get("priority"):
            tickets = [t for t in tickets if getattr(t, "priority", None) == query["priority"]]

        # Sort by creation date (newest first)
        tickets.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        return tickets

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, ticket_data: Any):
        ticket = {
            "ticketNumber": self.generateTicketNumber(),
            "user": getattr(ticket_data, "user", None),
            "name": getattr(ticket_data, "name", None),
            "email": getattr(ticket_data, "email", None),
            "phone": getattr(ticket_data, "phone", None),
            "company": getattr(ticket_data, "company", None),
            "subject": ticket_data.subject,
            "description": ticket_data.description,
            "category": getattr(ticket_data, "category", "general"),
            "priority": getattr(ticket_data, "priority", "medium"),
            "status": getattr(ticket_data, "status", "open"),
            "attachments": getattr(ticket_data, "attachments", []),
            "assignedTo": getattr(ticket_data, "assignedTo", None),
            "responses": [],
            "resolvedAt": None,
            "closedAt": None,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        return await self.storage.create(ticket)

    async def update(self, id: str, update_data: Any):
        if getattr(update_data, "status", None) == "resolved" and "resolvedAt" not in update_data:
            update_data.resolvedAt = datetime.now(timezone.utc).isoformat()
        elif getattr(update_data, "status", None) == "closed" and "closedAt" not in update_data:
            update_data.closedAt = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

    async def addResponse(self, ticket_id: str, response_data: Any):
        ticket = await self.findById(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        response = {
            "user": response_data.user,
            "message": response_data.message,
            "attachments": getattr(response_data, "attachments", []),
            "isAdminResponse": getattr(response_data, "isAdminResponse", False),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        ticket.responses = getattr(ticket, "responses", [])
        ticket.responses.append(response)

        # Update ticket status if admin responds
        if getattr(response_data, "isAdminResponse", None) and getattr(ticket, "status", None) == "open":
            ticket.status = "in_progress"

        return await self.update(ticket_id, {"responses": ticket.responses, "status": ticket.status})

    async def delete(self, id: str):
        return await self.storage.delete(id)


support_ticket_repository = SupportTicketRepository()
