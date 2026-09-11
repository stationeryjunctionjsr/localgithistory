from typing import Dict, Any, List
from app.models.schemas import MessageResponse
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.utils.auth import require_super_admin
from app.utils.logger import logger

router = APIRouter()


@router.get("/{page_id}", response_model=Dict[str, Any])
async def get_page_info(page_id: str, current_user: dict = Depends(require_super_admin)):
    """Get page information for super admin"""
    try:
        page_info_path = Path(__file__).parent.parent.parent / "data" / "page-info.json"

        if not page_info_path.exists():
            return {"page": None, "columns": {}}

        with open(page_info_path, "r", encoding="utf-8") as f:
            page_info = json.load(f)

        page_data = page_info.get("pages", {}).get(page_id)

        if not page_data:
            return {"page": None, "columns": {}}

        return {
            "page": {"title": page_data.get("title"), "description": page_data.get("description")},
            "columns": page_data.get("columns", {}),
        }
    except Exception as e:
        logger.error("get_page_info failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Server error")


@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
async def get_all_page_info(current_user: dict = Depends(require_super_admin)):
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
