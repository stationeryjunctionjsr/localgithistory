from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.user import User
from app.models.schemas import MessageResponse, SellerPayoutDetailResponse, MarkPaidRequest
from app.models.daos import SellerPayoutInternalCreate, SellerPayoutInternalUpdate
from app.models.sub_order import SubOrderInternalUpdate
from app.db.storage_factory import get_storage
from app.utils.auth import get_current_user, is_seller_admin, require_super_admin, require_super_admin_or_seller
from app.utils.logger import logger
from app.repositories.sub_order_repository import sub_order_repository
from app.repositories.user_repository import user_repository

"""
Seller Payout Ledger Router

Tracks actual cash disbursements from the platform to sellers.
Commissions move: unrealized -> realized (automatic after return window)
                   realized -> pending_payment (when payout created) -> admin_paid -> seller_received
"""

router = APIRouter()

PAYOUT_COLLECTION = "sellerPayouts"

def _payout_storage():
    return get_storage(PAYOUT_COLLECTION)

class SellerPayoutCreate(CamelBaseModel):
    seller_id: str
    amount: float = Field(..., ge=0)
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    status: Optional[str] = 'pending_payment'
    notes: Optional[str] = None
    sub_order_ids: Optional[List[str]] = Field(default=[], description="Sub-order IDs included in this payout")

class SellerPayoutSummaryResponse(BaseModel):
    seller_id: str
    sellerName: Optional[str] = None
    totalRealized: float
    totalPaid: float
    totalOutstanding: float
    totalUnrealized: float
    totalPayoutRealized: float
    totalPayoutPaid: float
    totalPayoutOutstanding: float
    totalPayoutUnrealized: float
    totalValueRealized: float
    totalTaxRealized: float
    subOrderCount: int


async def _enrich_with_seller(doc: SellerPayoutDetailResponse) -> SellerPayoutDetailResponse:
    seller = await user_repository.findById(doc.seller_id)
    if seller:
        doc.seller_name = seller.company_name or seller.name or ""
        doc.seller_upi_id = seller.upi_id
        doc.seller_qr_code_url = seller.qr_code_url
        doc.seller_bank_account_number = seller.bank_account_number
        doc.seller_bank_ifsc_code = seller.bank_ifsc_code
        doc.seller_bank_account_holder = seller.bank_account_holder
        doc.seller_bank_name = seller.bank_name
    return doc

@router.get("", response_model=List[SellerPayoutDetailResponse])
@router.get("/", response_model=List[SellerPayoutDetailResponse])
async def list_seller_payouts(
    seller_id: Optional[str] = Query(None),
    current_user: User = Depends(require_super_admin_or_seller)):
    storage = _payout_storage()
    query: dict = {}
    if is_seller_admin(current_user):
        query["sellerId"] = str(current_user.id)
    elif seller_id:
        query["sellerId"] = seller_id

    records = await storage.findAll(query)
    for r in records:
        await _enrich_with_seller(r)
    return records


@router.post("", response_model=SellerPayoutDetailResponse, status_code=201)
@router.post("/", response_model=SellerPayoutDetailResponse, status_code=201)
async def create_seller_payout(
    data: SellerPayoutCreate,
    current_user: User = Depends(require_super_admin)):
    seller = await user_repository.findById(data.sellerId)
    if not seller or not seller.is_seller_admin:
        raise HTTPException(status_code=404, detail="Seller not found")

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    storage = _payout_storage()
    created = await storage.create(
        SellerPayoutInternalCreate(
            sellerId=data.sellerId,
            amount=data.amount,
            periodStart=data.periodStart,
            periodEnd=data.periodEnd,
            status=data.status or "pending_payment",
            notes=data.notes,
            subOrderIds=data.sub_order_ids or []
        )
    )

    for so_id in data.sub_order_ids or []:
        try:
            await sub_order_repository.update(so_id, SubOrderInternalUpdate(commissionStatus="paid"))
        except Exception as e:
            logger.warning("Failed to mark sub-order %s as commission paid: %s", so_id, e, exc_info=True)

    await _enrich_with_seller(created)
    created.created_by = str(current_user.id)
    return created

@router.post("/settle-all/{seller_id}", response_model=SellerPayoutDetailResponse, status_code=201)
async def settle_all_seller_payouts(
    seller_id: str,
    current_user: User = Depends(require_super_admin)):
    seller = await user_repository.findById(seller_id)
    if not seller or not seller.is_seller_admin:
        raise HTTPException(status_code=404, detail="Seller not found")

    sub_orders = await sub_order_repository.findAll({"sellerId": seller_id, "commissionStatus": "realized"})
    if not sub_orders:
        raise HTTPException(status_code=400, detail="No realized sub-orders found to settle")

    total_amount = sum(float(so.total) - float(so.commission_amount) for so in sub_orders)
    sub_order_ids = [str(so.id) for so in sub_orders]
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    storage = _payout_storage()
    created = await storage.create(
        SellerPayoutInternalCreate(
            sellerId=seller_id,
            amount=round(total_amount, 2),
            status="pending_payment",
            notes="Bulk settlement of all realized sub-orders",
            subOrderIds=sub_order_ids
        )
    )

    for so_id in sub_order_ids:
        try:
            await sub_order_repository.update(so_id, SubOrderInternalUpdate(commissionStatus="paid"))
        except Exception as e:
            logger.warning("Failed to mark sub-order %s as commission paid: %s", so_id, e, exc_info=True)

    await _enrich_with_seller(created)
    created.created_by = str(current_user.id)
    return created

@router.post("/{payout_id}/mark-paid", response_model=SellerPayoutDetailResponse)
async def mark_payout_paid(
    payout_id: str,
    data: MarkPaidRequest,
    current_user: User = Depends(require_super_admin)):
    storage = _payout_storage()
    existing = await storage.findById(payout_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Payout not found")
        
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    updated = await storage.update(
        payout_id,
        SellerPayoutInternalUpdate(
            status="admin_paid",
            adminPaidAt=now,
            adminPaidBy=str(current_user.id),
            paymentMethod=data.payment_method,
            paymentReference=data.payment_reference,
            notes=data.notes if data.notes else existing.notes
        )
    )
    
    await _enrich_with_seller(updated)
    return updated

@router.post("/{payout_id}/mark-received", response_model=SellerPayoutDetailResponse)
async def mark_payout_received(
    payout_id: str,
    current_user: User = Depends(require_super_admin_or_seller)):
    storage = _payout_storage()
    existing = await storage.findById(payout_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Payout not found")
        
    if is_seller_admin(current_user) and existing.seller_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update this payout")
        
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    updated = await storage.update(
        payout_id,
        SellerPayoutInternalUpdate(
            status="seller_received",
            sellerReceivedAt=now
        )
    )
    
    await _enrich_with_seller(updated)
    return updated

@router.get("/my-summary", response_model=SellerPayoutSummaryResponse)
async def get_my_seller_payout_summary(
    current_user: User = Depends(get_current_user)):
    if not is_seller_admin(current_user):
        raise HTTPException(status_code=403, detail="Only sellers can access this endpoint")
    return await _get_seller_summary(str(current_user.id))

@router.get("/summary/{seller_id}", response_model=SellerPayoutSummaryResponse)
async def get_seller_payout_summary(
    seller_id: str,
    current_user: User = Depends(require_super_admin)):
    return await _get_seller_summary(seller_id)

@router.get("/summaries", response_model=List[SellerPayoutSummaryResponse])
async def get_all_seller_payout_summaries(
    current_user: User = Depends(require_super_admin)):
    import asyncio
    sellers = await user_repository.findAll({"role": "wholesaler", "isSellerAdmin": True})
    tasks = [_get_seller_summary(str(seller.id)) for seller in sellers]
    results = await asyncio.gather(*tasks)

    for i, seller in enumerate(sellers):
        results[i].seller_name = seller.company_name or seller.name or "Unknown"

    return results


async def _get_seller_summary(seller_id: str) -> SellerPayoutSummaryResponse:
    sub_orders = await sub_order_repository.findAll({"sellerId": seller_id})

    comm_realized = sum(float(so.commission_amount) for so in sub_orders if so.commission_status in ("realized", "paid"))
    comm_paid = sum(float(so.commission_amount) for so in sub_orders if so.commission_status == "paid")
    comm_unrealized = sum(float(so.commission_amount) for so in sub_orders if so.commission_status == "unrealized")

    val_realized = sum(float(so.total) for so in sub_orders if so.commission_status in ("realized", "paid"))
    val_paid = sum(float(so.total) for so in sub_orders if so.commission_status == "paid")
    val_unrealized = sum(float(so.total) for so in sub_orders if so.commission_status == "unrealized")

    tax_realized = sum(float(so.tax) for so in sub_orders if so.commission_status in ("realized", "paid"))

    payout_realized = round(val_realized - comm_realized, 2)
    payout_paid = round(val_paid - comm_paid, 2)
    payout_unrealized = round(val_unrealized - comm_unrealized, 2)
    payout_outstanding = round(payout_realized - payout_paid, 2)

    return SellerPayoutSummaryResponse(
        sellerId=seller_id,
        totalRealized=round(comm_realized, 2),
        totalPaid=round(comm_paid, 2),
        totalOutstanding=round(comm_realized - comm_paid, 2),
        totalUnrealized=round(comm_unrealized, 2),
        totalPayoutRealized=payout_realized,
        totalPayoutPaid=payout_paid,
        totalPayoutOutstanding=payout_outstanding,
        totalPayoutUnrealized=payout_unrealized,
        totalValueRealized=round(val_realized, 2),
        totalTaxRealized=round(tax_realized, 2),
        subOrderCount=len(sub_orders))
