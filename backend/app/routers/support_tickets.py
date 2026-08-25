from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.models.schemas import SupportTicketCreate, TicketResponseCreate
from app.repositories.support_ticket_repository import support_ticket_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, get_optional_user, require_super_admin

router = APIRouter()


class StatusUpdate(BaseModel):
    status: str
    assignedTo: Optional[str] = None


class PriorityUpdate(BaseModel):
    priority: str


async def populate_ticket(ticket):
    """Populate ticket with user data"""
    user = await user_repository.findById(ticket.get("user"))
    assigned_to = None
    if ticket.get("assignedTo"):
        assigned_to = await user_repository.findById(ticket["assignedTo"])

    # Populate response users
    populated_responses = []
    for response in ticket.get("responses", []):
        response_user = await user_repository.findById(response.get("user"))
        populated_responses.append(
            {
                **response,
                "user": {
                    "_id": response_user.get("_id"),
                    "name": response_user.get("name"),
                    "email": response_user.get("email"),
                    "role": response_user.get("role"),
                }
                if response_user
                else None,
            }
        )

    return {
        **ticket,
        "user": {
            "_id": user.get("_id") if user else None,
            "name": user.get("name") if user else ticket.get("name"),
            "email": user.get("email") if user else ticket.get("email"),
            "role": user.get("role") if user else "guest",
        },
        "assignedTo": {
            "_id": assigned_to.get("_id"),
            "name": assigned_to.get("name"),
            "email": assigned_to.get("email"),
        }
        if assigned_to
        else None,
        "responses": populated_responses,
    }


@router.get("", response_model=List[dict])
@router.get("/", response_model=List[dict])
async def get_support_tickets(
    status: Optional[str] = None, priority: Optional[str] = None, current_user: dict = Depends(get_current_user)
):
    query = {}

    if current_user.get("role") != "super_admin":
        query["user"] = current_user.get("_id")

    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority

    tickets = await support_ticket_repository.findAll(query)
    populated_tickets = [await populate_ticket(ticket) for ticket in tickets]

    return populated_tickets


@router.get("/{ticket_id}", response_model=dict)
async def get_support_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    ticket = await support_ticket_repository.findById(ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if current_user.get("role") != "super_admin" and ticket.get("user") != current_user.get("_id"):
        raise HTTPException(status_code=403, detail="Access denied")

    populated_ticket = await populate_ticket(ticket)
    return populated_ticket


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_support_ticket(
    ticket_data: SupportTicketCreate, current_user: Optional[dict] = Depends(get_optional_user)
):
    ticket = await support_ticket_repository.create(
        {
            "user": current_user.get("_id") if current_user else None,
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


@router.put("/{ticket_id}/status", response_model=dict)
async def update_ticket_status(
    ticket_id: str, status_data: StatusUpdate, current_user: dict = Depends(require_super_admin)
):
    ticket = await support_ticket_repository.findById(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = {"status": status_data.status}
    if status_data.assignedTo:
        update_data["assignedTo"] = status_data.assignedTo

    updated_ticket = await support_ticket_repository.update(ticket_id, update_data)
    populated_ticket = await populate_ticket(updated_ticket)

    return populated_ticket


@router.post("/{ticket_id}/response", response_model=dict)
async def add_ticket_response(
    ticket_id: str, response_data: TicketResponseCreate, current_user: dict = Depends(get_current_user)
):
    ticket = await support_ticket_repository.findById(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if current_user.get("role") != "super_admin" and ticket.get("user") != current_user.get("_id"):
        raise HTTPException(status_code=403, detail="Access denied")

    is_admin_response = current_user.get("role") == "super_admin"

    await support_ticket_repository.addResponse(
        ticket_id,
        {
            "user": current_user.get("_id"),
            "message": response_data.message,
            "attachments": response_data.attachments or [],
            "isAdminResponse": is_admin_response,
        },
    )

    updated_ticket = await support_ticket_repository.findById(ticket_id)
    populated_ticket = await populate_ticket(updated_ticket)

    return populated_ticket


@router.put("/{ticket_id}/priority", response_model=dict)
async def update_ticket_priority(
    ticket_id: str, priority_data: PriorityUpdate, current_user: dict = Depends(require_super_admin)
):
    ticket = await support_ticket_repository.update(ticket_id, {"priority": priority_data.priority})

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    populated_ticket = await populate_ticket(ticket)
    return populated_ticket
