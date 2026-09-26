from datetime import datetime
from typing import Dict, List, Optional, Any
import re
from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.storage_factory import get_storage
from app.utils.logger import logger

from app.models.daos import ReturnRequestInternalCreate, ReturnRequestInternalUpdate, ReturnRequestInternal

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
        table_name = f"sj_return_requests"
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
        all_requests = await self.findAll()
        max_id = 0

        for req in all_requests:
            req_id = req.id or req.returnId or ""
            match = re.match(f"{re.escape(prefix)}(\\d+)", req_id)
            if match:
                max_id = max(max_id, int(match.group(1)))
        next_id = max(1, max_id + 1)
        return f"{prefix}{next_id}"

    async def findAll(self, query: Optional[Dict] = None) -> List[ReturnRequestInternal]:
        requests = await self.storage.findAll(query)
        if not query:
            requests.sort(key=lambda x: x.created_at or "", reverse=True)
        return requests

    async def findById(self, id: str) -> Optional[ReturnRequestInternal]:
        return await self.storage.findById(id)

    async def findByOrderId(self, order_id: str) -> List[ReturnRequestInternal]:
        return await self.findAll({"orderId": order_id})

    async def create(self, data: ReturnRequestInternalCreate) -> ReturnRequestInternal:
        return_id = await self.generateReturnId()
        data.returnId = return_id
        if data.status is None:
            data.status = "pending"
        if data.valetCascadeCount is None:
            data.valetCascadeCount = 0
        if data.valetDeclineHistory is None:
            data.valetDeclineHistory = []
        if data.delivery_charge is None:
            data.delivery_charge = 0

        return await self.storage.create(data)

    async def update(self, id: str, update_data: ReturnRequestInternalUpdate) -> ReturnRequestInternal:
        return await self.storage.update(id, update_data)

    async def delete(self, id: str) -> Dict:
        return await self.storage.delete(id)


return_request_repository = ReturnRequestRepository()
