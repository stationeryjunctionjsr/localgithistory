import secrets
from datetime import datetime, timezone
from typing import Optional, List

from app.db.storage_factory import get_storage
from app.models.daos_flat import SupportTicketInternalCreate, SupportTicketInternalUpdate
from app.models.schemas import SupportTicketInternal, TicketResponseItemInternal


class SupportTicketRepository:
    def __init__(self):
        self.storage = get_storage("supportTickets")

    def generateTicketNumber(self) -> str:
        return f"TKT-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{secrets.token_hex(4).upper()}"

    async def findAll(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[SupportTicketInternal]:
        tickets = await self.storage.findAll(status=status, user_id=user_id, priority=priority)

        if user_id:
            tickets = [t for t in tickets if t.user == user_id]

        if status:
            tickets = [t for t in tickets if t.status == status]

        if priority:
            tickets = [t for t in tickets if t.priority == priority]

        # Sort by creation date (newest first)
        tickets.sort(key=lambda x: x.created_at, reverse=True)

        return tickets

    async def findById(self, id: int) -> Optional[SupportTicketInternal]:
        return await self.storage.findById(id)

    async def create(self, ticket_data: SupportTicketInternalCreate) -> SupportTicketInternal:
        if not ticket_data.ticket_number:
            ticket_data.ticket_number = self.generateTicketNumber()
        if not ticket_data.created_at:
            ticket_data.created_at = datetime.now(timezone.utc).isoformat()
        
        return await self.storage.create(ticket_data)

    async def update(self, id: int, update_data: SupportTicketInternalUpdate) -> SupportTicketInternal:
        if update_data.status == "resolved" and update_data.resolvedAt is None:
            update_data.resolvedAt = datetime.now(timezone.utc).isoformat()
        elif update_data.status == "closed" and update_data.closedAt is None:
            update_data.closedAt = datetime.now(timezone.utc).isoformat()

        return await self.storage.update(id, update_data)

    async def addResponse(self, ticket_id: int, user: str, message: str, attachments: list[str], is_admin_response: bool) -> SupportTicketInternal:
        ticket = await self.findById(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        new_resp = TicketResponseItemInternal(user=user, message=message, attachments=attachments, isAdminResponse=is_admin_response)

        responses: list[TicketResponseItemInternal] = []
        if ticket.responses:
            for r in ticket.responses:
                responses.append(TicketResponseItemInternal(user=r.user, message=r.message, attachments=r.attachments, isAdminResponse=r.isAdminResponse))

        responses.append(new_resp)

        new_status = ticket.status
        if is_admin_response and ticket.status == "open":
            new_status = "in_progress"

        update_payload = SupportTicketInternalUpdate(
            status=new_status,
            responses=responses
        )

        return await self.update(ticket_id, update_payload)

    async def delete(self, id: int) -> bool:
        return await self.storage.delete(id)


support_ticket_repository = SupportTicketRepository()
