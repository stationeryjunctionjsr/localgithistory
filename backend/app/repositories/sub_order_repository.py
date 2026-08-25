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

    async def create(self, data: Dict) -> Dict:
        sub_order = {
            "subOrderNumber": data["subOrderNumber"],
            "parentOrderId": data["parentOrderId"],
            "parentOrderNumber": data["parentOrderNumber"],
            "sellerId": data.get("sellerId"),  # None = platform / super_admin
            "sellerName": data.get("sellerName", ""),
            "user": data["user"],
            "items": data.get("items", []),
            "subtotal": float(data.get("subtotal", 0)),
            "tax": float(data.get("tax", 0)),
            "shipping": float(data.get("shipping", 0)),
            "deliveryGst": float(data.get("deliveryGst", 0)),
            "discount": float(data.get("discount", 0)),
            "total": float(data.get("total", 0)),
            "orderType": data.get("orderType", "b2c"),
            "status": data.get("status", "pending"),
            "paymentMethod": data.get("paymentMethod", "cod"),
            "paymentStatus": data.get("paymentStatus", "pending"),
            "isUrgentDelivery": data.get("isUrgentDelivery", False),
            "deliverySlot": data.get("deliverySlot"),
            "shippingAddress": data.get("shippingAddress", {}),
            "billingAddress": data.get("billingAddress", {}),
            "notes": data.get("notes", ""),
            "couponCode": data.get("couponCode"),
            "couponInfo": data.get("couponInfo"),
            "assignedValet": data.get("assignedValet"),
            # Pickup tracking — valet confirms collection from each seller individually
            "pickupStatus": data.get("pickupStatus", "pending_pickup"),  # 'pending_pickup' | 'picked_up'
            "pickedUpAt": data.get("pickedUpAt"),
            "shippedAt": data.get("shippedAt"),
            "deliveredAt": data.get("deliveredAt"),
            "cancelledAt": data.get("cancelledAt"),
            "cancelledBy": data.get("cancelledBy"),
            "declineReason": data.get("declineReason"),
            # Commission fields — populated when delivered
            "commissionPct": None,
            "commissionAmount": None,
            "commissionStatus": None,  # None | 'unrealized' | 'realized'
            "createdAt": data.get("createdAt") or datetime.now(timezone.utc).isoformat(),
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

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        # Mirror status-specific timestamps from order_repository
        if update_data.get("status") == "out_for_delivery" and "shippedAt" not in update_data:
            update_data["shippedAt"] = datetime.now(timezone.utc).isoformat()
        if update_data.get("status") == "delivered" and "deliveredAt" not in update_data:
            update_data["deliveredAt"] = datetime.now(timezone.utc).isoformat()
        if update_data.get("status") == "shipped" and "shippedAt" not in update_data:
            update_data["shippedAt"] = datetime.now(timezone.utc).isoformat()
        if update_data.get("status") == "cancelled" and "cancelledAt" not in update_data:
            update_data["cancelledAt"] = datetime.now(timezone.utc).isoformat()
        # Auto-stamp pickedUpAt when valet confirms collection from this seller
        if update_data.get("pickupStatus") == "picked_up" and "pickedUpAt" not in update_data:
            update_data["pickedUpAt"] = datetime.now(timezone.utc).isoformat() + "Z"

        # Stamp commission when transitioning to 'delivered' (only if not already set)
        if update_data.get("status") == "delivered" and "commissionPct" not in update_data:
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
