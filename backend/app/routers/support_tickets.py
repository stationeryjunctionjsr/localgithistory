from app.models.user import User
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict

from app.models.schemas import SupportTicketCreate, TicketResponseCreate, SupportTicketResponse
from app.repositories.support_ticket_repository import support_ticket_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, get_optional_user, require_super_admin

router = APIRouter()


class StatusUpdate(BaseModel):
    status: str
    assignedTo: Optional[str] = None


class PriorityUpdate(BaseModel):
    priority: str


class TicketResponseItem(BaseModel):
    user: Optional[Any] = None
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
    createdAt: Optional[str] = None

    model_config = ConfigDict(extra="allow")


async def populate_ticket(ticket):
    """Populate ticket with user data"""
    t_user = ticket.user
    t_assigned_to = ticket.assignedTo
    t_responses = ticket.responses
    
    user = await user_repository.findById(t_user)
    assigned_to = None
    if t_assigned_to:
        assigned_to = await user_repository.findById(t_assigned_to)

    # Populate response users
    populated_responses = []
    for response in (t_responses or []):
        resp_model = (
            response
            if isinstance(response, TicketResponseItem)
            else TicketResponseItem.model_validate(response)
        )
        user_val = resp_model.user
        user_id_str = (
            user_val
            if isinstance(user_val, str)
            else (
                user_val.id
                )
            )
        
        response_user = await user_repository.findById(user_id_str) if user_id_str else None
        resp_dict = response if isinstance(response, dict) else resp_model.model_dump()
        populated_responses.append(
            {
                **resp_dict,
                "user": {
                    "_id": response_user.id,
                    "name": response_user.name,
                    "email": response_user.email,
                    "role": response_user.role,
                }
                if response_user
                else None,
            }
        )

    assigned_to_dict = None
    if assigned_to:
        assigned_to_dict = {
            "_id": assigned_to.id,
            "name": assigned_to.name,
            "email": assigned_to.email,
        }

    return {
        **ticket,
        "user": {
            "_id": user.id if user else None,
            "name": user.name if user else (ticket.name),
            "email": user.email if user else (ticket.email),
            "role": user.role if user else "guest",
        },
        "assignedTo": assigned_to_dict,
        "responses": populated_responses,
    }


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
    ticket_data: SupportTicketCreate, current_user: Optional[dict] = Depends(get_optional_user)
):
    ticket = await support_ticket_repository.create(
        {
            "user": current_user.id if current_user else None,
            "name": ticket_data.name,
            "email": ticket_data.email,
            "phone": ticket_data.phone,
            "company": ticket_data.company,
            "subject": ticket_data.subject,
            "description": ticket_data.description,
            "category": ticket_data.category or "general",
            "priority": ticket_data.priority or "medium",
            "attachments": ticket_data.attachments or [],
        }
    )

    populated_ticket = await populate_ticket(ticket)
    return populated_ticket


@router.put("/{ticket_id}/status", response_model=SupportTicketResponse)
async def update_ticket_status(
    ticket_id: str, status_data: StatusUpdate, current_user: User = Depends(require_super_admin)
):
    ticket = await support_ticket_repository.findById(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = {"status": status_data.status}
    if status_data.assignedTo:
        update_data.assignedTo = status_data.assignedTo

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
        ticket_id,
        {
            "user": current_user.id,
            "message": response_data.message,
            "attachments": response_data.attachments or [],
            "isAdminResponse": is_admin_response,
        },
    )

    updated_ticket = await support_ticket_repository.findById(ticket_id)
    populated_ticket = await populate_ticket(updated_ticket)

    return populated_ticket


@router.put("/{ticket_id}/priority", response_model=SupportTicketResponse)
async def update_ticket_priority(
    ticket_id: str, priority_data: PriorityUpdate, current_user: User = Depends(require_super_admin)
):
    ticket = await support_ticket_repository.update(ticket_id, {"priority": priority_data.priority})

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    populated_ticket = await populate_ticket(ticket)
    return populated_ticket
