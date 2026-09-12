from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.storage_factory import get_storage
from app.utils.logger import logger


class SubOrderRepository:
    def __init__(self):
        self.storage = get_storage("subOrders")

    def _generate_sub_order_number(self, parent_order_number: str, index: int) -> str:
        """Generate sub-order number by appending a letter suffix to the parent order number.
        e.g. ORDER-RT-42 -> ORDER-RT-42-A, ORDER-RT-42-B, etc.
        """
        suffix = chr(ord("A") + index)
        return f"{parent_order_number}-{suffix}"

    async def create(self, data: Any) -> Dict:
        sub_order = {
            "subOrderNumber": data.subOrderNumber,
            "parentOrderId": data.parentOrderId,
            "parentOrderNumber": data.parentOrderNumber,
            "sellerId": getattr(data, "sellerId", None),  # None = platform / super_admin
            "sellerName": getattr(data, 'sellerName', ""),
            "user": data.user,
            "items": getattr(data, 'items', []),
            "subtotal": float(getattr(data, 'subtotal', 0)),
            "tax": float(getattr(data, 'tax', 0)),
            "shipping": float(getattr(data, 'shipping', 0)),
            "deliveryGst": float(getattr(data, 'deliveryGst', 0)),
            "discount": float(getattr(data, 'discount', 0)),
            "total": float(getattr(data, 'total', 0)),
            "orderType": getattr(data, 'orderType', "b2c"),
            "status": getattr(data, 'status', "pending"),
            "paymentMethod": getattr(data, 'paymentMethod', "cod"),
            "paymentStatus": getattr(data, 'paymentStatus', "pending"),
            "isUrgentDelivery": getattr(data, 'isUrgentDelivery', False),
            "deliverySlot": getattr(data, "deliverySlot", None),
            "shippingAddress": getattr(data, 'shippingAddress', {}),
            "billingAddress": getattr(data, 'billingAddress', {}),
            "notes": getattr(data, 'notes', ""),
            "couponCode": getattr(data, "couponCode", None),
            "couponInfo": getattr(data, "couponInfo", None),
            "assignedValet": getattr(data, "assignedValet", None),
            # Pickup tracking — valet confirms collection from each seller individually
            "pickupStatus": getattr(data, 'pickupStatus', "pending_pickup"),  # 'pending_pickup' | 'picked_up'
            "pickedUpAt": getattr(data, "pickedUpAt", None),
            "shippedAt": getattr(data, "shippedAt", None),
            "deliveredAt": getattr(data, "deliveredAt", None),
            "cancelledAt": getattr(data, "cancelledAt", None),
            "cancelledBy": getattr(data, "cancelledBy", None),
            "declineReason": getattr(data, "declineReason", None),
            # Commission fields — populated when delivered
            "commissionPct": None,
            "commissionAmount": None,
            "commissionStatus": None,  # None | 'unrealized' | 'realized'
            "createdAt": getattr(data, "createdAt", None) or datetime.now(timezone.utc).isoformat(),
        }
        return await self.storage.create(sub_order)

    async def findAll(
        self, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict]:
        try:
            return await self.storage.findAll(query or {}, skip=skip, limit=limit)
        except TypeError:
            docs = await self.storage.findAll(query or {})
            if skip is not None or limit is not None:
                start = skip or 0
                end = (start + limit) if limit is not None else None
                return docs[start:end]
            return docs

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def findByParentOrder(self, parent_order_id: str) -> List[Dict]:
        return await self.storage.findAll({"parentOrderId": parent_order_id})

    async def findBySeller(
        self, seller_id: str, query: Optional[Dict] = None, skip: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict]:
        q = dict(query or {})
        q["sellerId"] = seller_id
        return await self.findAll(q, skip=skip, limit=limit)

    async def count(self, query: Optional[Dict] = None) -> int:
        if hasattr(self.storage, "count"):
            return await self.storage.count(query or {})
        docs = await self.storage.findAll(query or {})
        return len(docs)

    async def update(self, id: str, update_data: Any) -> Optional[Dict]:
        # Mirror status-specific timestamps from order_repository
        if getattr(update_data, "status", None) == "out_for_delivery" and "shippedAt" not in update_data:
            update_data.shippedAt = datetime.now(timezone.utc).isoformat()
        if getattr(update_data, "status", None) == "delivered" and "deliveredAt" not in update_data:
            update_data.deliveredAt = datetime.now(timezone.utc).isoformat()
        if getattr(update_data, "status", None) == "shipped" and "shippedAt" not in update_data:
            update_data.shippedAt = datetime.now(timezone.utc).isoformat()
        if getattr(update_data, "status", None) == "cancelled" and "cancelledAt" not in update_data:
            update_data.cancelledAt = datetime.now(timezone.utc).isoformat()
        # Auto-stamp pickedUpAt when valet confirms collection from this seller
        if getattr(update_data, "pickupStatus", None) == "picked_up" and "pickedUpAt" not in update_data:
            update_data.pickedUpAt = datetime.now(timezone.utc).isoformat() + "Z"

        # Stamp commission when transitioning to 'delivered' (only if not already set)
        if getattr(update_data, "status", None) == "delivered" and "commissionPct" not in update_data:
            existing = await self.storage.findById(id)
            if existing and existing.get("commissionStatus") is None:
                try:
                    from app.routers.commission import stamp_commission_on_delivery

                    commission_fields = await stamp_commission_on_delivery(existing)
                    update_data.update(commission_fields)
                    # Ensure deliveredAt is in the existing snapshot for realize-check
                    if "deliveredAt" not in commission_fields:
                        update_data.setdefault("deliveredAt", datetime.now(timezone.utc).isoformat())
                except Exception as e:
                    logger.warning("Could not stamp commission on delivery for sub-order %s: %s", id, e)

        return await self.storage.update(id, update_data)

    async def delete(self, id: str):
        return await self.storage.delete(id)


sub_order_repository = SubOrderRepository()
