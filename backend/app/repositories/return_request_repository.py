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
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
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
        parsed_requests = []
        for r in requests:
            if isinstance(r, dict):
                parsed_requests.append(ReturnRequestInternal.model_validate(r))
            else:
                parsed_requests.append(ReturnRequestInternal.model_validate(r, from_attributes=True))
                
        if not query:
            parsed_requests.sort(key=lambda x: x.createdAt or "", reverse=True)
        return parsed_requests

    async def findById(self, id: str) -> Optional[ReturnRequestInternal]:
        data = await self.storage.findById(id)
        if data:
            if isinstance(data, dict):
                return ReturnRequestInternal.model_validate(data)
            return ReturnRequestInternal.model_validate(data, from_attributes=True)
        return None

    async def findByOrderId(self, order_id: str) -> List[ReturnRequestInternal]:
        return await self.findAll({"orderId": order_id})

    async def create(self, data: Any) -> ReturnRequestInternal:
        if isinstance(data, dict):
            model = ReturnRequestInternalCreate.model_validate(data)
        else:
            model = ReturnRequestInternalCreate.model_validate(data, from_attributes=True)
            
        return_id = await self.generateReturnId()
        model.id = return_id
        model.returnId = return_id
        if getattr(model, 'status', None) is None:
            model.status = "pending"
        if getattr(model, 'valetCascadeCount', None) is None:
            model.valetCascadeCount = 0
        if getattr(model, 'valetDeclineHistory', None) is None:
            model.valetDeclineHistory = []
        if getattr(model, 'deliveryCharge', None) is None:
            model.deliveryCharge = 0
        
        now_iso = datetime.utcnow().isoformat()
        if getattr(model, 'createdAt', None) is None:
            model.createdAt = now_iso
        if getattr(model, 'updatedAt', None) is None:
            model.updatedAt = now_iso

        created_data = await self.storage.create(model)
        
        if isinstance(created_data, dict):
            return ReturnRequestInternal.model_validate(created_data)
        return ReturnRequestInternal.model_validate(created_data, from_attributes=True)

    async def update(self, id: str, update_data: Any) -> ReturnRequestInternal:
        if isinstance(update_data, dict):
            model = ReturnRequestInternalUpdate.model_validate(update_data)
        else:
            model = ReturnRequestInternalUpdate.model_validate(update_data, from_attributes=True)
            
        model.updatedAt = datetime.utcnow().isoformat()
        
        updated_data = await self.storage.update(id, model)
        
        if isinstance(updated_data, dict):
            return ReturnRequestInternal.model_validate(updated_data)
        return ReturnRequestInternal.model_validate(updated_data, from_attributes=True)

    async def delete(self, id: str) -> Dict:
        return await self.storage.delete(id)


return_request_repository = ReturnRequestRepository()
