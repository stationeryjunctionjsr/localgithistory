import secrets
from datetime import datetime, timezone
from typing import Dict, Optional, Any

from app.db.storage_factory import get_storage
from app.models.daos_flat import SupportTicketInternalCreate, SupportTicketInternalUpdate


class SupportTicketRepository:
    def __init__(self):
        self.storage = get_storage("supportTickets")

    def generateTicketNumber(self) -> str:
        return f"TKT-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{secrets.token_hex(4).upper()}"

    async def findAll(self, query: Optional[Dict] = None):
        tickets = await self.storage.findAll()

        query = query or {}

        if "user" in query and query["user"]:
            tickets = [t for t in tickets if t.user == query["user"]]

        if "status" in query and query["status"]:
            tickets = [t for t in tickets if t.status == query["status"]]

        if "priority" in query and query["priority"]:
            tickets = [t for t in tickets if t.priority == query["priority"]]

        # Sort by creation date (newest first)
        tickets.sort(key=lambda x: x.createdAt, reverse=True)

        return tickets

    async def findById(self, id: str):
        return await self.storage.findById(id)

    async def create(self, ticket_data: Any):
        if isinstance(ticket_data, dict):
            from app.models.daos_flat import SupportTicketInternalCreate
            if 'ticketNumber' not in ticket_data:
                ticket_data['ticketNumber'] = self.generateTicketNumber()
            if 'createdAt' not in ticket_data:
                from datetime import datetime, timezone
                ticket_data['createdAt'] = datetime.now(timezone.utc).isoformat()
            ticket_data = SupportTicketInternalCreate(**ticket_data)
        internal_data = SupportTicketInternalCreate(
            ticketNumber=self.generateTicketNumber(),
            user=ticket_data.user,
            name=ticket_data.name,
            email=ticket_data.email,
            phone=ticket_data.phone,
            company=ticket_data.company,
            subject=ticket_data.subject,
            description=ticket_data.description,
            category=ticket_data.category if ticket_data.category is not None else "general",
            priority=ticket_data.priority if ticket_data.priority is not None else "medium",
            status=ticket_data.status if ticket_data.status is not None else "open",
            attachments=ticket_data.attachments if ticket_data.attachments is not None else [],
            assignedTo=ticket_data.assignedTo,
            responses=[],
            resolvedAt=None,
            closedAt=None,
            createdAt=datetime.now(timezone.utc).isoformat()
        )

        return await self.storage.create(internal_data)

    async def update(self, id: str, update_data: Any):
        if not isinstance(update_data, SupportTicketInternalUpdate):
            internal_update = SupportTicketInternalUpdate(
                status=update_data.status,
                resolvedAt=update_data.resolvedAt if update_data.resolvedAt is not None else None,
                closedAt=update_data.closedAt if update_data.closedAt is not None else None,
                responses=update_data.responses if update_data.responses is not None else None
            )
        else:
            internal_update = update_data

        if internal_update.status == "resolved" and internal_update.resolvedAt is None:
            internal_update.resolvedAt = datetime.now(timezone.utc).isoformat()
        elif internal_update.status == "closed" and internal_update.closedAt is None:
            internal_update.closedAt = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, internal_update)

    async def addResponse(self, ticket_id: str, response_data: Any):
        ticket = await self.findById(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        response = {
            "user": response_data.user,
            "message": response_data.message,
            "attachments": response_data.attachments if response_data.attachments is not None else [],
            "isAdminResponse": response_data.isAdminResponse if response_data.isAdminResponse is not None else False,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

        if ticket.responses is None:
            ticket.responses = []
            
        ticket.responses.append(response)

        # Update ticket status if admin responds
        if response_data.isAdminResponse and ticket.status == "open":
            ticket.status = "in_progress"

        update_payload = SupportTicketInternalUpdate(
            status=ticket.status,
            responses=ticket.responses,
            resolvedAt=ticket.resolvedAt,
            closedAt=ticket.closedAt
        )

        return await self.update(ticket_id, update_payload)

    async def delete(self, id: str):
        return await self.storage.delete(id)


support_ticket_repository = SupportTicketRepository()
