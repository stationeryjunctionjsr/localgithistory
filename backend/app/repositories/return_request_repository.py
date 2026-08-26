from datetime import datetime
from typing import Dict, List, Optional
import re
from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.storage_factory import get_storage
from app.utils.logger import logger


class ReturnRequestRepository:
    def __init__(self):
        self._storage = None
        self._columns_checked = False

    @property
    def storage(self):
        if self._storage is None:
            self._storage = get_storage("returnRequests")
        return self._storage

    async def ensure_table_columns(self):
        if self._columns_checked:
            return
        factory = get_async_session_factory()
        if not factory:
            self._columns_checked = True
            return
        suffix = getattr(settings, "table_suffix", "")
        table_name = f"sj_return_requests{suffix}"
        columns_to_add = [
            ("seller_id", "VARCHAR(64) NULL"),
            ("delivery_slot_id", "VARCHAR(64) NULL"),
            ("delivery_slot_config_id", "VARCHAR(64) NULL"),
            ("delivery_slot_date", "VARCHAR(32) NULL"),
            ("pending_valet_id", "VARCHAR(64) NULL"),
            ("valet_assigned_at", "DATETIME NULL"),
            ("valet_cascade_count", "INT DEFAULT 0"),
            ("valet_accepted_at", "DATETIME NULL"),
            ("valet_declined_at", "DATETIME NULL"),
            ("valet_decline_reason", "VARCHAR(1000) NULL"),
            ("valet_decline_history", "LONGTEXT NULL"),
        ]
        try:
            async with factory() as session:
                result = await session.execute(text(f"SHOW COLUMNS FROM {table_name}"))
                existing_cols = {row[0].lower() for row in result.fetchall()}
                for col_name, col_def in columns_to_add:
                    if col_name.lower() not in existing_cols:
                        logger.info("Adding missing column %s to %s", col_name, table_name)
                        await session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN `{col_name}` {col_def}"))
                await session.commit()
            self._columns_checked = True
        except Exception as e:
            logger.warning("Could not verify/alter table columns for %s: %s", table_name, e)
            self._columns_checked = True

    async def generateReturnId(self) -> str:
        prefix = "RET-"
        all_requests = await self.storage.findAll()
        max_id = 0

        for req in all_requests:
            match = re.match(f"{re.escape(prefix)}(\\d+)", req.get("id", "") or req.get("returnId", ""))
            if match:
                max_id = max(max_id, int(match.group(1)))
        next_id = max(1, max_id + 1)
        return f"{prefix}{next_id}"

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        requests = await self.storage.findAll(query)
        if not query:
            requests.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        return requests

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.storage.findById(id)

    async def findByOrderId(self, order_id: str) -> List[Dict]:
        return await self.findAll({"orderId": order_id})

    async def create(self, data: Dict) -> Dict:
        return_id = await self.generateReturnId()
        request = {
            "id": return_id,
            "returnId": return_id,
            "orderId": data["orderId"],
            "userId": data["userId"],
            "items": data["items"],
            "paymentMethod": data["paymentMethod"],
            "upiPaymentScreenshot": data.get("upiPaymentScreenshot"),
            "notes": data.get("notes"),
            "status": data.get("status", "pending"),
            "sellerId": data.get("sellerId"),
            "deliverySlotId": data.get("deliverySlotId"),
            "deliverySlotConfigId": data.get("deliverySlotConfigId"),
            "deliverySlotDate": data.get("deliverySlotDate"),
            "valetId": data.get("valetId"),
            "pendingValetId": data.get("pendingValetId"),
            "valetAssignedAt": data.get("valetAssignedAt"),
            "valetCascadeCount": data.get("valetCascadeCount", 0),
            "valetDeclineHistory": data.get("valetDeclineHistory", []),
            "valetAcceptedAt": data.get("valetAcceptedAt"),
            "valetDeclinedAt": data.get("valetDeclinedAt"),
            "valetDeclineReason": data.get("valetDeclineReason"),
            "deliveryCharge": data.get("deliveryCharge", 0),
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat(),
        }
        return await self.storage.create(request)

    async def update(self, id: str, update_data: Dict) -> Dict:
        update_data["updatedAt"] = datetime.utcnow().isoformat()
        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> Dict:
        return await self.storage.delete(id)


return_request_repository = ReturnRequestRepository()
