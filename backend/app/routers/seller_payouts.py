from app.models.schemas import MessageResponse
"""
Seller Payout Ledger Router

Tracks actual cash disbursements from the platform to sellers.
Commissions move: unrealized -> realized (automatic after return window)
                   realized -> paid (admin manually marks as paid via this router)

Endpoints:
  GET  /seller-payouts                    – List all payout records (admin: all; seller: own)
  POST /seller-payouts                    – Admin creates a payout record
  GET  /seller-payouts/summary/{seller_id} – Realized, paid, and outstanding totals
  GET  /seller-payouts/my-summary         – Same but for authenticated seller
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.db.storage_factory import get_storage
from app.utils.auth import get_current_user, is_seller_admin, require_super_admin, require_super_admin_or_seller
from app.utils.logger import logger

router = APIRouter()

PAYOUT_COLLECTION = "sellerPayouts"
SUB_ORDER_COLLECTION = "sub_orders"


def _payout_storage():
    return get_storage(PAYOUT_COLLECTION)


class SellerPayoutCreate(BaseModel):
    sellerId: str
    amount: float = Field(..., ge=0)
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    notes: Optional[str] = None
    subOrderIds: Optional[List[str]] = Field(default=[], description="Sub-order IDs included in this payout")


class SellerPayoutResponse(BaseModel):
    id: str
    sellerId: str
    sellerName: Optional[str] = None
    amount: float
    periodStart: Optional[str] = None
    periodEnd: Optional[str] = None
    status: str  # "paid"
    notes: Optional[str] = None
    subOrderIds: List[str] = []
    createdBy: Optional[str] = None
    paidAt: str
    createdAt: str


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
async def list_seller_payouts(
    seller_id: Optional[str] = Query(None),
    current_user: dict = Depends(require_super_admin_or_seller),
):
    """List payout records. Sellers see only their own records. Admins can filter by seller_id."""
    storage = _payout_storage()
    query: Dict[str, Any] = {}

    if is_seller_admin(current_user):
        # Sellers only see their own payouts
        query["sellerId"] = str(current_user["_id"])
    elif seller_id:
        query["sellerId"] = seller_id

    records = await storage.findAll(query)
    return records


@router.post("", response_model=Dict[str, Any], status_code=201)
@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_seller_payout(
    data: SellerPayoutCreate,
    current_user: dict = Depends(require_super_admin),
):
    """Record a payout to a seller (Super Admin only). Marks the included sub-orders as commission paid."""
    from app.repositories.sub_order_repository import sub_order_repository
    from app.repositories.user_repository import user_repository

    seller = await user_repository.findById(data.sellerId)
    if not seller or not seller.is_seller_admin:
        raise HTTPException(status_code=404, detail="Seller not found")

    now = datetime.now(timezone.utc).isoformat() + "Z"
    payout_doc = {
        "sellerId": data.sellerId,
        "sellerName": seller.company_name or seller.name or "",
        "amount": data.amount,
        "periodStart": data.periodStart,
        "periodEnd": data.periodEnd,
        "status": "paid",
        "notes": data.notes,
        "subOrderIds": data.subOrderIds or [],
        "createdBy": str(current_user["_id"]),
        "paidAt": now,
        "createdAt": now,
    }

    storage = _payout_storage()
    created = await storage.create(payout_doc)

    # Mark included sub-orders as commission paid
    for so_id in data.subOrderIds or []:
        try:
            await sub_order_repository.update(so_id, {"commissionStatus": "paid", "commissionPaidAt": now})
        except Exception as e:
            logger.warning("Failed to mark sub-order %s as commission paid: %s", so_id, e)

    return created


@router.post("/settle-all/{seller_id}", response_model=Dict[str, Any], status_code=201)
async def settle_all_seller_payouts(
    seller_id: str,
    current_user: dict = Depends(require_super_admin),
):
    """Settle all realized sub-orders for a seller."""
    from app.repositories.sub_order_repository import sub_order_repository
    from app.repositories.user_repository import user_repository

    seller = await user_repository.findById(seller_id)
    if not seller or not seller.is_seller_admin:
        raise HTTPException(status_code=404, detail="Seller not found")

    # Fetch all realized sub-orders
    sub_orders = await sub_order_repository.findAll({"sellerId": seller_id, "commissionStatus": "realized"})

    if not sub_orders:
        raise HTTPException(status_code=400, detail="No realized sub-orders found to settle")

    # Calculate total payout
    total_amount = sum(float(so.total or 0) - float(so.commission_amount or 0) for so in sub_orders)

    sub_order_ids = [str(so["_id"]) for so in sub_orders]

    now = datetime.now(timezone.utc).isoformat() + "Z"
    payout_doc = {
        "sellerId": seller_id,
        "sellerName": seller.company_name or seller.name or "",
        "amount": round(total_amount, 2),
        "status": "paid",
        "notes": "Bulk settlement of all realized sub-orders",
        "subOrderIds": sub_order_ids,
        "createdBy": str(current_user["_id"]),
        "paidAt": now,
        "createdAt": now,
    }

    storage = _payout_storage()
    created = await storage.create(payout_doc)

    # Mark included sub-orders as paid
    for so_id in sub_order_ids:
        try:
            await sub_order_repository.update(so_id, {"commissionStatus": "paid", "commissionPaidAt": now})
        except Exception as e:
            logger.warning("Failed to mark sub-order %s as commission paid: %s", so_id, e)

    return created


@router.get("/my-summary", response_model=Dict[str, Any])
async def get_my_seller_payout_summary(
    current_user: dict = Depends(get_current_user),
):
    """Get payout summary for the authenticated seller."""
    if not is_seller_admin(current_user):
        raise HTTPException(status_code=403, detail="Only sellers can access this endpoint")
    return await _get_seller_summary(str(current_user["_id"]))


@router.get("/summary/{seller_id}", response_model=Dict[str, Any])
async def get_seller_payout_summary(
    seller_id: str,
    current_user: dict = Depends(require_super_admin),
):
    """Get payout summary for a specific seller (Super Admin only)."""
    return await _get_seller_summary(seller_id)


@router.get("/summaries", response_model=Dict[str, Any])
async def get_all_seller_payout_summaries(
    current_user: dict = Depends(require_super_admin),
):
    """Get payout summaries for all sellers (Super Admin only)."""
    import asyncio

    from app.repositories.user_repository import user_repository

    sellers = await user_repository.findAll({"role": "wholesaler", "isSellerAdmin": True})

    tasks = []
    for seller in sellers:
        seller_id = str(seller["_id"])
        tasks.append(_get_seller_summary(seller_id))

    results = await asyncio.gather(*tasks)

    # Merge seller name into the summary
    for i, seller in enumerate(sellers):
        results[i]["sellerName"] = seller.company_name or seller.name or "Unknown"

    return results


async def _get_seller_summary(seller_id: str) -> Dict[str, Any]:
    """Compute realized, paid, and outstanding payout and commission totals for a seller."""
    from app.repositories.sub_order_repository import sub_order_repository

    sub_orders = await sub_order_repository.findAll({"sellerId": seller_id})

    # Commission values
    comm_realized = sum(
        float(so.commission_amount or 0)
        for so in sub_orders
        if so.commission_status in ("realized", "paid")
    )
    comm_paid = sum(float(so.commission_amount or 0) for so in sub_orders if so.commission_status == "paid")
    comm_unrealized = sum(
        float(so.commission_amount or 0) for so in sub_orders if so.commission_status == "unrealized"
    )

    # Sub-order values
    val_realized = sum(
        float(so.total or 0) for so in sub_orders if so.commission_status in ("realized", "paid")
    )
    val_paid = sum(float(so.total or 0) for so in sub_orders if so.commission_status == "paid")
    val_unrealized = sum(float(so.total or 0) for so in sub_orders if so.commission_status == "unrealized")

    # Tax (GST) values
    tax_realized = sum(
        float(so.tax or 0) for so in sub_orders if so.commission_status in ("realized", "paid")
    )
    tax_paid = sum(float(so.tax or 0) for so in sub_orders if so.commission_status == "paid")
    tax_unrealized = sum(float(so.tax or 0) for so in sub_orders if so.commission_status == "unrealized")

    # Net Payout (Sub-order Value - Commission)
    payout_realized = round(val_realized - comm_realized, 2)
    payout_paid = round(val_paid - comm_paid, 2)
    payout_unrealized = round(val_unrealized - comm_unrealized, 2)
    payout_outstanding = round(payout_realized - payout_paid, 2)

    return {
        "sellerId": seller_id,
        # Commission metrics
        "totalRealized": round(comm_realized, 2),
        "totalPaid": round(comm_paid, 2),
        "totalOutstanding": round(comm_realized - comm_paid, 2),
        "totalUnrealized": round(comm_unrealized, 2),
        # Payout metrics
        "totalPayoutRealized": payout_realized,
        "totalPayoutPaid": payout_paid,
        "totalPayoutOutstanding": payout_outstanding,
        "totalPayoutUnrealized": payout_unrealized,
        # Sub-order value and tax metrics
        "totalValueRealized": round(val_realized, 2),
        "totalTaxRealized": round(tax_realized, 2),
        "subOrderCount": len(sub_orders),
    }
