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
            tickets = [t for t in tickets if t.user == query["user"]]

        if query.get("status"):
            tickets = [t for t in tickets if t.status == query["status"]]

        if query.get("priority"):
            tickets = [t for t in tickets if t.priority == query["priority"]]

        # Sort by creation date (newest first)
        tickets.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        return tickets

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, ticket_data: Any):
        ticket = {
            "ticketNumber": self.generateTicketNumber(),
            "user": ticket_data.user,
            "name": ticket_data.name,
            "email": ticket_data.email,
            "phone": ticket_data.phone,
            "company": ticket_data.company,
            "subject": ticket_data.subject,
            "description": ticket_data.description,
            "category": (ticket_data.category if ticket_data.category is not None else "general"),
            "priority": (ticket_data.priority if ticket_data.priority is not None else "medium"),
            "status": (ticket_data.status if ticket_data.status is not None else "open"),
            "attachments": (ticket_data.attachments if ticket_data.attachments is not None else []),
            "assignedTo": ticket_data.assignedTo,
            "responses": [],
            "resolvedAt": None,
            "closedAt": None,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        return await self.storage.create(ticket)

    async def update(self, id: str, update_data: Any):
        if update_data.status == "resolved" and "resolvedAt" not in update_data:
            update_data.resolvedAt = datetime.now(timezone.utc).isoformat()
        elif update_data.status == "closed" and "closedAt" not in update_data:
            update_data.closedAt = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

    async def addResponse(self, ticket_id: str, response_data: Any):
        ticket = await self.findById(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        response = {
            "user": response_data.user,
            "message": response_data.message,
            "attachments": (response_data.attachments if response_data.attachments is not None else []),
            "isAdminResponse": (response_data.isAdminResponse if response_data.isAdminResponse is not None else False),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        ticket.responses = (ticket.responses if ticket.responses is not None else [])
        ticket.responses.append(response)

        # Update ticket status if admin responds
        if response_data.isAdminResponse and ticket.status == "open":
            ticket.status = "in_progress"

        return await self.update(ticket_id, {"responses": ticket.responses, "status": ticket.status})

    async def delete(self, id: str):
        return await self.storage.delete(id)


support_ticket_repository = SupportTicketRepository()
