import secrets
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List

from app.db.storage_factory import get_storage
from app.models.daos_flat import SupportTicketInternalCreate, SupportTicketInternalUpdate
from app.models.schemas import SupportTicketInternal, TicketResponseItemInternal


class SupportTicketRepository:
    def __init__(self):
        self.storage = get_storage("supportTickets")

    def generateTicketNumber(self) -> str:
        return f"TKT-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{secrets.token_hex(4).upper()}"

    async def findAll(self, query: Optional[Dict] = None) -> List[SupportTicketInternal]:
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

    async def findById(self, id: str) -> Optional[SupportTicketInternal]:
        return await self.storage.findById(id)

    async def create(self, ticket_data: SupportTicketInternalCreate) -> SupportTicketInternal:
        if not ticket_data.ticketNumber:
            ticket_data.ticketNumber = self.generateTicketNumber()
        if not ticket_data.createdAt:
            ticket_data.createdAt = datetime.now(timezone.utc).isoformat()
        
        return await self.storage.create(ticket_data)

    async def update(self, id: str, update_data: SupportTicketInternalUpdate) -> SupportTicketInternal:
        if update_data.status == "resolved" and update_data.resolvedAt is None:
            update_data.resolvedAt = datetime.now(timezone.utc).isoformat()
        elif update_data.status == "closed" and update_data.closedAt is None:
            update_data.closedAt = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

    async def addResponse(self, ticket_id: str, user: str, message: str, attachments: list[str], is_admin_response: bool) -> SupportTicketInternal:
        ticket = await self.findById(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        new_resp = TicketResponseItemInternal(user=user, message=message, attachments=attachments)

        responses: list[TicketResponseItemInternal] = []
        if ticket.responses:
            for r in ticket.responses:
                responses.append(TicketResponseItemInternal(user=r.user, message=r.message, attachments=r.attachments))

        responses.append(new_resp)

        new_status = ticket.status
        if is_admin_response and ticket.status == "open":
            new_status = "in_progress"

        update_payload = SupportTicketInternalUpdate(
            status=new_status,
            responses=responses
        )

        return await self.update(ticket_id, update_payload)

    async def delete(self, id: str) -> bool:
        return await self.storage.delete(id)


support_ticket_repository = SupportTicketRepository()
