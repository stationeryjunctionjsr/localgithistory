from app.models.user import User
from typing import Dict, Any, List, Optional
from app.models.schemas import MessageResponse
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.utils.auth import require_super_admin
from app.utils.logger import logger


from pydantic import BaseModel, Field, ConfigDict


class PageDetail(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    columns: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class PageInfoContainer(BaseModel):
    pages: Dict[str, PageDetail] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class PageInfoResponse(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    page: Optional[Dict[str, str]] = None
    columns: Optional[Dict[str, str]] = None
    pages: Optional[Dict[str, PageDetail]] = None

    model_config = ConfigDict(extra="forbid")


router = APIRouter()


@router.get("/{page_id}", response_model=PageInfoResponse)
async def get_page_info(page_id: str, current_user: User = Depends(require_super_admin)):
    """Get page information for super admin"""
    try:
        page_info_path = Path(__file__).parent.parent.parent / "data" / "page-info.json"

        if not page_info_path.exists():
            return {"page": None, "columns": {}}

        with open(page_info_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        container = PageInfoContainer.model_validate(raw_data)
        page_data = container.pages[page_id] if page_id in container.pages else None

        if not page_data:
            return {"page": None, "columns": {}}

        return {
            "page": {"title": page_data.title, "description": page_data.description},
            "columns": page_data.columns,
        }
    except Exception as e:
        logger.error("get_page_info failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")


@router.get("", response_model=List[PageInfoResponse])
@router.get("/", response_model=List[PageInfoResponse])
async def get_all_page_info(current_user: User = Depends(require_super_admin)):
    """Get all page information for super admin"""
    try:
        page_info_path = Path(__file__).parent.parent.parent / "data" / "page-info.json"

        if not page_info_path.exists():
            return {"pages": {}}

        with open(page_info_path, "r", encoding="utf-8") as f:
            page_info = json.load(f)

        return page_info
    except Exception as e:
        logger.error("get_all_page_info failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")
