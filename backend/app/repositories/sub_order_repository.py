import logging
from datetime import datetime, timezone
from typing import List, Optional

from app.models.sub_order import (
    SubOrderInternalCreate,
    SubOrderInternalUpdate,
    SubOrder,
    SubOrderFilter,
)
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

    async def create(self, data: SubOrderInternalCreate) -> SubOrder:
        if not data.created_at:
            data.created_at = datetime.now(timezone.utc).isoformat()
        return await self.storage.create(data)

    async def findAll(
        self,
        filter_params: Optional[SubOrderFilter] = None,
        skip: int = 0,
        limit: int = 0,
    ) -> List[SubOrder]:
        return await self.storage.findAll(filter_params, skip=skip, limit=limit)

    async def findById(self, id: int) -> Optional[SubOrder]:
        return await self.storage.findById(id)

    async def findByParentOrder(self, parent_order_id: str) -> List[SubOrder]:
        return await self.storage.findByParentOrder(parent_order_id)

    async def findBySeller(
        self,
        seller_id: str,
        filter_params: Optional[SubOrderFilter] = None,
        skip: int = 0,
        limit: int = 0,
    ) -> List[SubOrder]:
        return await self.storage.findBySeller(seller_id, filter_params=filter_params, skip=skip, limit=limit)

    async def count(self, filter_params: Optional[SubOrderFilter] = None) -> int:
        return await self.storage.count(filter_params)

    async def update(self, id: int, update_data: SubOrderInternalUpdate) -> Optional[SubOrder]:
        if update_data.status == "out_for_delivery" and update_data.shipped_at is None:
            update_data.shipped_at = datetime.now(timezone.utc).isoformat()
        if update_data.status == "delivered" and update_data.delivered_at is None:
            update_data.delivered_at = datetime.now(timezone.utc).isoformat()
        if update_data.status == "shipped" and update_data.shipped_at is None:
            update_data.shipped_at = datetime.now(timezone.utc).isoformat()
        if update_data.status == "cancelled" and update_data.cancelled_at is None:
            update_data.cancelled_at = datetime.now(timezone.utc).isoformat()
        if update_data.pickup_status == "picked_up" and update_data.picked_up_at is None:
            update_data.picked_up_at = datetime.now(timezone.utc).isoformat() + "Z"

        if update_data.status == "delivered" and update_data.commission_pct is None:
            existing = await self.storage.findById(id)
            if existing and existing.commission_status is None:
                try:
                    from app.routers.commission import stamp_commission_on_delivery
                    commission = await stamp_commission_on_delivery(existing)
                    if commission.commission_status is not None:
                        update_data.commission_status = commission.commission_status
                    if commission.commission_pct is not None:
                        update_data.commission_pct = commission.commission_pct
                    if commission.commission_amount is not None:
                        update_data.commission_amount = commission.commission_amount
                    if not update_data.delivered_at:
                        update_data.delivered_at = datetime.now(timezone.utc).isoformat()
                except Exception as e:
                    logging.warning("sub_order_repository.update: commission stamp failed for sub-order %r: %s", id, e, exc_info=e)

        return await self.storage.update(id, update_data)

    async def delete(self, id: int):
        return await self.storage.delete(id)


sub_order_repository = SubOrderRepository()
