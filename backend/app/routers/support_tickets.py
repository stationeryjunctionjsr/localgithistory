from app.models.user import User
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict

from app.models.schemas import SupportTicketCreate, TicketResponseCreate, SupportTicketResponse, SupportTicketBase, SupportTicketInternal
from app.repositories.support_ticket_repository import support_ticket_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, get_optional_user, require_super_admin

router = APIRouter()


class StatusUpdate(BaseModel):
    status: str
    assignedTo: Optional[str] = None


class PriorityUpdate(BaseModel):
    priority: str


from app.models.daos_flat import SupportTicketInternalCreate, SupportTicketInternalUpdate
from app.models.schemas import UserSnippet, TicketResponseItem


async def populate_ticket(ticket_data):
    """Populate ticket with user data"""
    # Strictly validate incoming raw data into internal model where user is a string ID
    ticket = SupportTicketInternal.model_validate(ticket_data, from_attributes=True)

    user = await user_repository.findById(ticket.user) if ticket.user else None
    assigned_to = await user_repository.findById(ticket.assigned_to) if ticket.assigned_to else None

    # Populate response users
    populated_responses = []
    for response in (ticket.responses or []):
        resp_user_id_str = response.user
        response_user = await user_repository.findById(resp_user_id_str) if resp_user_id_str else None
        
        # Build Pydantic model natively
        new_resp_model = TicketResponseItem.model_validate(response, from_attributes=True)
        if response_user:
            new_resp_model.user = UserSnippet(
                _id=response_user.id,
                name=response_user.name,
                email=response_user.email,
                role=response_user.role,
            )
        populated_responses.append(new_resp_model)

    final_assigned_to = None
    if assigned_to:
        final_assigned_to = UserSnippet(
            _id=assigned_to.id,
            name=assigned_to.name,
            email=assigned_to.email,
        )

    if user:
        final_user = UserSnippet(
            _id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
        )
    else:
        final_user = UserSnippet(
            _id=None,
            name=ticket.name,
            email=ticket.email,
            role="guest"
        )
        
    return SupportTicketResponse(
        _id=ticket.id,
        name=ticket.name,
        email=ticket.email,
        phone=ticket.phone,
        company=ticket.company,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        attachments=ticket.attachments,
        ticket_number=ticket.ticket_number,
        status=ticket.status,
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        external_id=ticket.external_id,
        user=final_user,
        assigned_to=final_assigned_to,
        responses=populated_responses
    )


@router.get("", response_model=List[SupportTicketResponse])
@router.get("/", response_model=List[SupportTicketResponse])
async def get_support_tickets(
    status: Optional[str] = None, priority: Optional[str] = None, current_user: User = Depends(get_current_user)
):
    query = {}

    if current_user.role != "super_admin":
        query["user"] = current_user.id

    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority

    tickets = await support_ticket_repository.findAll(query)
    populated_tickets = [await populate_ticket(ticket) for ticket in tickets]

    return populated_tickets


@router.get("/{ticket_id}", response_model=SupportTicketResponse)
async def get_support_ticket(ticket_id: str, current_user: User = Depends(get_current_user)):
    ticket = await support_ticket_repository.findById(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if current_user.role != "super_admin" and ticket.user != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    populated_ticket = await populate_ticket(ticket)
    return populated_ticket


@router.post("", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
async def create_support_ticket(
    ticket_data: SupportTicketCreate, current_user: Optional[User] = Depends(get_optional_user)
):
    internal_data = SupportTicketInternalCreate(
        ticketNumber="",
        user=current_user.id if current_user else None,
        name=ticket_data.name,
        email=ticket_data.email,
        phone=ticket_data.phone,
        company=ticket_data.company,
        subject=ticket_data.subject,
        description=ticket_data.description,
        category=ticket_data.category or "general",
        priority=ticket_data.priority or "medium",
        attachments=ticket_data.attachments or [],
    )
    ticket = await support_ticket_repository.create(internal_data)

    populated_ticket = await populate_ticket(ticket)
    return populated_ticket


@router.put("/{ticket_id}/status", response_model=SupportTicketResponse)
async def update_ticket_status(
    ticket_id: str, status_data: StatusUpdate, current_user: User = Depends(require_super_admin)
):
    ticket = await support_ticket_repository.findById(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = SupportTicketInternalUpdate(
        status=status_data.status,
        assignedTo=status_data.assignedTo if status_data.assignedTo else None,
    )

    updated_ticket = await support_ticket_repository.update(ticket_id, update_data)
    populated_ticket = await populate_ticket(updated_ticket)

    return populated_ticket


@router.post("/{ticket_id}/response", response_model=SupportTicketResponse)
async def add_ticket_response(
    ticket_id: str, response_data: TicketResponseCreate, current_user: User = Depends(get_current_user)
):
    ticket = await support_ticket_repository.findById(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if current_user.role != "super_admin" and ticket.user != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    is_admin_response = current_user.role == "super_admin"

    await support_ticket_repository.addResponse(
        ticket_id=ticket_id,
        user=current_user.id,
        message=response_data.message,
        attachments=response_data.attachments or [],
        is_admin_response=is_admin_response,
    )

    updated_ticket = await support_ticket_repository.findById(ticket_id)
    populated_ticket = await populate_ticket(updated_ticket)

    return populated_ticket


@router.put("/{ticket_id}/priority", response_model=SupportTicketResponse)
async def update_ticket_priority(
    ticket_id: str, priority_data: PriorityUpdate, current_user: User = Depends(require_super_admin)
):
    update_data = SupportTicketInternalUpdate(priority=priority_data.priority)
    ticket = await support_ticket_repository.update(ticket_id, update_data)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    populated_ticket = await populate_ticket(ticket)
    return populated_ticket
