from typing import List, Optional

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


def _populate_response_item(
    response: SellerRequestResponseItem,
    admin_user: Optional[UserSnippet] = None,
) -> TicketResponseItem:
    return TicketResponseItem(
        user=admin_user,
        message=response.response or "",
        attachments=[],
        created_at=response.created_at,
    )


async def _build_users_map(requests: List[SellerRequest]) -> dict[str, UserSnippet]:
    user_ids: set[str] = set()
    for req in requests:
        if req.user:
            user_ids.add(str(req.user))
        for resp in (req.responses or []):
            if resp.admin_id:
                user_ids.add(str(resp.admin_id))

    if not user_ids:
        return {}

    users = await user_repository.findByIds(list(user_ids))
    return {
        str(u.id): UserSnippet(
            id=u.id,
            name=u.name or "Unknown",
            email=u.email or "Unknown",
            role=u.role or "unknown",
        )
        for u in users
        if u.id
    }


def _map_request(request: SellerRequest, users_map: dict[str, UserSnippet]) -> SellerRequestResponse:
    user_snippet = users_map.get(str(request.user)) if request.user else None
    populated_responses: List[TicketResponseItem] = [
        _populate_response_item(resp, users_map.get(str(resp.admin_id)) if resp.admin_id else None)
        for resp in (request.responses or [])
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


async def populate_request(request: SellerRequest) -> SellerRequestResponse:
    """Populate single request with user data"""
    users_map = await _build_users_map([request])
    return _map_request(request, users_map)


@router.get("", response_model=List[SellerRequestResponse])
@router.get("/", response_model=List[SellerRequestResponse])
async def get_seller_requests(
    status: Optional[str] = None, priority: Optional[str] = None, current_user: User = Depends(get_current_user)
) -> List[SellerRequestResponse]:
    user_filter = current_user.id if current_user.role != "super_admin" else None
    requests = await seller_request_repository.findAll(user=user_filter, status=status, priority=priority)
    users_map = await _build_users_map(requests)
    return [_map_request(req, users_map) for req in requests]


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
