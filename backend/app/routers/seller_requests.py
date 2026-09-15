from app.models.user import User
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict

from app.models.schemas import SellerRequestCreate, SellerRequestResponseCreate, SellerRequestResponse
from app.repositories.seller_request_repository import seller_request_repository
from app.repositories.user_repository import user_repository
from app.utils.auth import get_current_user, require_super_admin

router = APIRouter()


class StatusUpdate(BaseModel):
    status: str


class SellerRequestResponseItem(BaseModel):
    user: Optional[Any] = None
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
    isAdminResponse: Optional[bool] = None
    createdAt: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


async def populate_request(request):
    """Populate request with user data"""
    user = await user_repository.findById(request.user)

    # Populate response users
    populated_responses = []
    for response in (request.responses if request.responses is not None else []):
        resp_model = (
            response
            if isinstance(response, SellerRequestResponseItem)
            else SellerRequestResponseItem.model_validate(response)
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

    return {
        **request,
        "user": {
            "_id": user.id if user else None,
            "name": user.name if user else "Unknown",
            "email": user.email if user else "Unknown",
            "role": user.role if user else "unknown",
        },
        "responses": populated_responses,
    }


@router.get("", response_model=List[SellerRequestResponse])
@router.get("/", response_model=List[SellerRequestResponse])
async def get_seller_requests(
    status: Optional[str] = None, priority: Optional[str] = None, current_user: User = Depends(get_current_user)
):
    query = {}

    if current_user.role != "super_admin":
        query["user"] = current_user.id

    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority

    requests = await seller_request_repository.findAll(query)
    populated_requests = [await populate_request(req) for req in requests]

    return populated_requests


@router.get("/{request_id}", response_model=SellerRequestResponse)
async def get_seller_request(request_id: str, current_user: User = Depends(get_current_user)):
    request = await seller_request_repository.findById(request_id)

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if current_user.role != "super_admin" and request.user != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    populated_request = await populate_request(request)
    return populated_request


@router.post("", response_model=SellerRequestResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=SellerRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_seller_request(request_data: SellerRequestCreate, current_user: User = Depends(get_current_user)):
    # Depending on requirements, we might want to restrict this to sellers only,
    # but super_admin can also create requests if they want, or we can check role.
    request = await seller_request_repository.create(
        {
            "user": current_user.id,
            "subject": request_data.subject,
            "description": request_data.description,
            "category": request_data.category or "general",
            "priority": request_data.priority or "medium",
            "attachments": request_data.attachments or [],
        }
    )

    populated_request = await populate_request(request)
    return populated_request


@router.put("/{request_id}/status", response_model=SellerRequestResponse)
async def update_request_status(
    request_id: str, status_data: StatusUpdate, current_user: User = Depends(require_super_admin)
):
    request = await seller_request_repository.findById(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    updated_request = await seller_request_repository.update(request_id, {"status": status_data.status})
    populated_request = await populate_request(updated_request)

    return populated_request


@router.post("/{request_id}/response", response_model=SellerRequestResponse)
async def add_request_response(
    request_id: str, response_data: SellerRequestResponseCreate, current_user: User = Depends(get_current_user)
):
    request = await seller_request_repository.findById(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if current_user.role != "super_admin" and request.user != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    is_admin_response = current_user.role == "super_admin"

    await seller_request_repository.addResponse(
        request_id,
        {
            "user": current_user.id,
            "message": response_data.message,
            "attachments": response_data.attachments or [],
            "isAdminResponse": is_admin_response,
        },
    )

    updated_request = await seller_request_repository.findById(request_id)
    populated_request = await populate_request(updated_request)

    return populated_request
