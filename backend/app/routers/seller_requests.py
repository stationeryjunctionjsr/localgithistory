from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.base import CamelBaseModel
from app.models.daos import SellerRequestInternalCreate, SellerRequestInternalUpdate
from app.models.schemas import (
    SellerRequestCreate,
    SellerRequestResponse,
    SellerRequestResponseCreate,
    TicketResponseItem,
    TicketResponseItemInternal,
    UserSnippet,
)
from app.models.seller_request import SellerRequest, SellerRequestResponseItem
from app.models.user import User
from app.repositories.seller_request_repository import seller_request_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, require_super_admin

router = APIRouter()


class StatusUpdate(CamelBaseModel):
    status: str


async def _populate_response_item(
    response: Union[SellerRequestResponseItem, TicketResponseItem, TicketResponseItemInternal],
) -> TicketResponseItem:
    if isinstance(response, SellerRequestResponseItem):
        admin_id = response.admin_id
        message = response.response
        created_at = response.created_at
        attachments: List[str] = []
    elif isinstance(response, TicketResponseItemInternal):
        admin_id = response.user
        message = response.message
        created_at = response.created_at
        attachments = response.attachments if response.attachments is not None else []
    elif isinstance(response, TicketResponseItem):
        admin_id = response.user.id if response.user is not None else None
        message = response.message
        created_at = response.created_at
        attachments = response.attachments if response.attachments is not None else []
    else:
        return response

    response_user = await user_repository.findById(admin_id) if admin_id is not None else None
    user_snippet = (
        UserSnippet(
            id=response_user.id,
            name=response_user.name if response_user.name is not None else "Unknown",
            email=response_user.email if response_user.email is not None else "Unknown",
            role=response_user.role if response_user.role is not None else "unknown",
        )
        if response_user is not None
        else None
    )

    return TicketResponseItem(
        user=user_snippet,
        message=message,
        attachments=attachments,
        created_at=created_at,
    )


async def populate_request(request: SellerRequest) -> SellerRequestResponse:
    """Populate request with user data"""
    user = await user_repository.findById(request.user) if request.user is not None else None

    user_snippet = (
        UserSnippet(
            id=user.id,
            name=user.name if user.name is not None else "Unknown",
            email=user.email if user.email is not None else "Unknown",
            role=user.role if user.role is not None else "unknown",
        )
        if user is not None
        else None
    )

    populated_responses: List[TicketResponseItem] = [
        await _populate_response_item(resp)
        for resp in (request.responses if request.responses is not None else [])
    ]

    return SellerRequestResponse(
        id=request.id if request.id is not None else request.external_id,
        subject=request.subject,
        description=request.description,
        category=request.category,
        priority=request.priority,
        status=request.status,
        user=user_snippet,
        attachments=request.attachments if request.attachments is not None else [],
        responses=populated_responses,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


@router.get("", response_model=List[SellerRequestResponse])
@router.get("/", response_model=List[SellerRequestResponse])
async def get_seller_requests(
    status: Optional[str] = None, priority: Optional[str] = None, current_user: User = Depends(get_current_user)
) -> List[SellerRequestResponse]:
    user_filter = current_user.id if current_user.role != "super_admin" else None
    requests = await seller_request_repository.findAll(user=user_filter, status=status, priority=priority)
    return [await populate_request(req) for req in requests]


@router.get("/{request_id}", response_model=SellerRequestResponse)
async def get_seller_request(
    request_id: str, current_user: User = Depends(get_current_user)
) -> SellerRequestResponse:
    request = await seller_request_repository.findById(request_id)

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if current_user.role != "super_admin" and request.user != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return await populate_request(request)


@router.post("", response_model=SellerRequestResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=SellerRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_seller_request(
    request_data: SellerRequestCreate, current_user: User = Depends(get_current_user)
) -> SellerRequestResponse:
    internal_data = SellerRequestInternalCreate(
        user=current_user.id,
        subject=request_data.subject,
        description=request_data.description,
        category=request_data.category if request_data.category is not None else "general",
        priority=request_data.priority if request_data.priority is not None else "medium",
        attachments=request_data.attachments if request_data.attachments is not None else [],
    )
    request = await seller_request_repository.create(internal_data)
    return await populate_request(request)


@router.put("/{request_id}/status", response_model=SellerRequestResponse)
async def update_request_status(
    request_id: str, status_data: StatusUpdate, current_user: User = Depends(require_super_admin)
) -> SellerRequestResponse:
    request = await seller_request_repository.findById(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    internal_update = SellerRequestInternalUpdate(status=status_data.status)
    updated_request = await seller_request_repository.update(request_id, internal_update)
    return await populate_request(updated_request)


@router.post("/{request_id}/response", response_model=SellerRequestResponse)
async def add_request_response(
    request_id: str, response_data: SellerRequestResponseCreate, current_user: User = Depends(get_current_user)
) -> SellerRequestResponse:
    request = await seller_request_repository.findById(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if current_user.role != "super_admin" and request.user != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    is_admin_response = current_user.role == "super_admin"

    response_payload = TicketResponseItemInternal(
        user=current_user.id,
        message=response_data.message,
        attachments=response_data.attachments if response_data.attachments is not None else [],
        is_admin_response=is_admin_response,
    )

    await seller_request_repository.addResponse(request_id, response_payload)

    updated_request = await seller_request_repository.findById(request_id)
    if not updated_request:
        raise HTTPException(status_code=404, detail="Request not found after update")

    return await populate_request(updated_request)
