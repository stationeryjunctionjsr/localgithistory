from app.models.user import User
from typing import List
from app.models.schemas import PincodeDetailsResponse, MessageResponse
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Query

from app.utils.auth import require_super_admin
from app.utils.cache import cache

router = APIRouter()

# Load pincode master data once at startup
_pincode_data = None


def _load_pincode_data():
    global _pincode_data
    if _pincode_data is None:
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "pincode_master.json")
        with open(data_path, "r") as f:
            _pincode_data = json.load(f)
    return _pincode_data


@router.get("/states", response_model=List[str])
@cache.ttl_cache(ttl=3600.0)
async def get_states():
    """Get all available states (public - used in checkout)"""
    data = _load_pincode_data()
    return sorted(data.keys())


@router.get("/districts", response_model=List[str])
@cache.ttl_cache(ttl=3600.0)
async def get_districts(state: str = Query(...)):
    """Get all districts for a given state (public - used in checkout)"""
    data = _load_pincode_data()
    if state not in data:
        raise HTTPException(status_code=404, detail=f"State '{state}' not found")
    return sorted(data[state].keys())


@router.get("/pincodes", response_model=List[str])
async def get_pincodes(
    state: str = Query(...), district: str = Query(...), current_user: User = Depends(require_super_admin)
):
    """Get all pincodes for a given state and district (admin only)"""
    data = _load_pincode_data()
    if state not in data:
        raise HTTPException(status_code=404, detail=f"State '{state}' not found")
    if district not in data[state]:
        raise HTTPException(status_code=404, detail=f"District '{district}' not found in state '{state}'")
    return sorted(data[state][district])


@router.get("/{pincode}", response_model=PincodeDetailsResponse)
async def get_pincode_details(pincode: str):
    """Reverse-lookup state and district for a given 6-digit pincode (public — used in checkout auto-fill)"""
    data = _load_pincode_data()
    for state, districts in data.items():
        for district, pincodes in districts.items():
            if pincode in pincodes:
                return {"state": state, "district": district, "city": district, "pincode": pincode}
    raise HTTPException(status_code=404, detail=f"Pincode '{pincode}' not found")
