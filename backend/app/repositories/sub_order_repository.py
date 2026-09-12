from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.models.sub_order import SubOrderInternalCreate, SubOrderInternalUpdate
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

    async def create(self, data: SubOrderInternalCreate) -> Dict:
        sub_order_dict = data.model_dump(exclude_unset=True)
        if not data.createdAt:
            sub_order_dict["createdAt"] = datetime.now(timezone.utc).isoformat()
        return await self.storage.create(sub_order_dict)

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

    async def update(self, id: str, update_data: SubOrderInternalUpdate) -> Optional[Dict]:
        if update_data.status == "out_for_delivery" and update_data.shippedAt is None:
            update_data.shippedAt = datetime.now(timezone.utc).isoformat()
        if update_data.status == "delivered" and update_data.deliveredAt is None:
            update_data.deliveredAt = datetime.now(timezone.utc).isoformat()
        if update_data.status == "shipped" and update_data.shippedAt is None:
            update_data.shippedAt = datetime.now(timezone.utc).isoformat()
        if update_data.status == "cancelled" and update_data.cancelledAt is None:
            update_data.cancelledAt = datetime.now(timezone.utc).isoformat()
        if update_data.pickupStatus == "picked_up" and update_data.pickedUpAt is None:
            update_data.pickedUpAt = datetime.now(timezone.utc).isoformat() + "Z"

        update_dict = update_data.model_dump(exclude_unset=True)

        if update_data.status == "delivered" and update_data.commissionPct is None:
            existing = await self.storage.findById(id)
            if existing and existing.get("commissionStatus") is None:
                try:
                    from app.routers.commission import stamp_commission_on_delivery
                    commission_fields = await stamp_commission_on_delivery(existing)
                    update_dict.update(commission_fields)
                    if "deliveredAt" not in commission_fields:
                        update_dict.setdefault("deliveredAt", datetime.now(timezone.utc).isoformat())
                except Exception as e:
                    pass

        return await self.storage.update(id, update_dict)

    async def delete(self, id: str):
        return await self.storage.delete(id)


sub_order_repository = SubOrderRepository()

