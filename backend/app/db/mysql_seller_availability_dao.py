from app.models.daos_flat import (
    SellerAvailabilityInternalCreate,
    SellerAvailabilityInternalUpdate,
    SellerAvailabilityFilter,
)
import logging
"""
MySQL DAO for seller availability windows.
Fully normalized storage: no doc JSON.
Table: sj_seller_availability
"""

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from app.models.seller_availability import SellerAvailability

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_dt(v) -> Optional[datetime]:
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v).replace("Z", ""))
    except Exception as e:
        logging.warning("mysql_seller_availability_dao._to_dt: could not parse datetime %r: %s", v, e, exc_info=e)
        return None


class MySQLSellerAvailabilityDAO:
    _COLUMN_MAP = {
        "seller_id": "seller_id",
        "status": "status",
        "start_at": "start_at",
        "end_at": "end_at",
        "reason": "reason",
        "created_by": "created_by",
        "cancelled_at": "cancelled_at",
    }

    @property
    def table_name(self) -> str:
        return "sj_seller_availability"

    def _get_session_factory(self):
        return get_async_session_factory()

    def __map_to_schema(self, row) -> 'SellerAvailability':
        return SellerAvailability.model_validate(row)

    async def findAll(
        self,
        filters: Optional[Union[SellerAvailabilityFilter, Dict[str, Any]]] = None,
        seller_id: Optional[str] = None,
        status: Optional[Union[str, List[str]]] = None,
        id: Optional[Union[str, int]] = None,
    ) -> List['SellerAvailability']:
        factory = self._get_session_factory()
        if not factory:
            return []

        where_clauses: List[str] = []
        params: Dict[str, Any] = {}

        target_id = id
        target_seller = seller_id
        target_status = status

        if filters is not None:
            if isinstance(filters, dict):
                if target_id is None and ("id" in filters or "_id" in filters):
                    target_id = filters.get("id") or filters.get("_id")
                if target_seller is None and ("seller_id" in filters or "sellerId" in filters):
                    target_seller = filters.get("seller_id") or filters.get("sellerId")
                if target_status is None and "status" in filters:
                    target_status = filters.get("status")
            elif isinstance(filters, SellerAvailabilityFilter):
                if target_id is None and filters.id is not None:
                    target_id = filters.id
                if target_seller is None and filters.seller_id is not None:
                    target_seller = filters.seller_id
                if target_status is None:
                    if filters.status is not None:
                        target_status = filters.status
                    elif filters.statuses is not None:
                        target_status = filters.statuses

        if target_id is not None:
            where_clauses.append("id = :q_id")
            params["q_id"] = int(target_id) if str(target_id).isdigit() else target_id

        if target_seller is not None:
            where_clauses.append("seller_id = :seller_id")
            params["seller_id"] = str(target_seller)

        if target_status is not None:
            if isinstance(target_status, dict) and "$in" in target_status:
                status_list = target_status["$in"]
                phs = [f":st_{i}" for i in range(len(status_list))]
                for i, st in enumerate(status_list):
                    params[f"st_{i}"] = str(st)
                where_clauses.append(f"status IN ({', '.join(phs)})" if phs else "1=0")
            elif isinstance(target_status, (list, tuple, set)):
                phs = [f":st_{i}" for i in range(len(target_status))]
                for i, st in enumerate(target_status):
                    params[f"st_{i}"] = str(st)
                where_clauses.append(f"status IN ({', '.join(phs)})" if phs else "1=0")
            else:
                where_clauses.append("status = :status")
                params["status"] = str(target_status)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, seller_id, status, start_at, end_at, reason, created_by, cancelled_at, created_at, updated_at FROM {self.table_name}{where_sql} ORDER BY created_at DESC"
                ),
                params,
            )
            return [self.__map_to_schema(r) for r in result.fetchall()]

    async def findOne(
        self,
        filters: Optional[Union[SellerAvailabilityFilter, Dict[str, Any]]] = None,
        seller_id: Optional[str] = None,
        status: Optional[Union[str, List[str]]] = None,
        id: Optional[Union[str, int]] = None,
    ) -> Optional['SellerAvailability']:
        docs = await self.findAll(filters=filters, seller_id=seller_id, status=status, id=id)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional['SellerAvailability']:
        return await self.findOne(id=id)

    async def create(self, data: SellerAvailabilityInternalCreate) -> 'SellerAvailability':
        factory = self._get_session_factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = datetime.now(timezone.utc)
        params = {
            "external_id": secrets.token_hex(16),
            "seller_id": str(data.seller_id or ""),
            "status": (data.status if data.status is not None else "scheduled"),
            "start_at": _to_dt(data.start_at),
            "end_at": _to_dt(data.end_at),
            "reason": data.reason,
            "created_by": data.created_by,
            "cancelled_at": _to_dt(getattr(data, "cancelled_at", None)),
            "created_at": now,
            "updated_at": now,
        }
        sql = text(f"""
            INSERT INTO {self.table_name}
                (external_id, seller_id, status, start_at, end_at, reason, created_by, cancelled_at, created_at, updated_at)
            VALUES
                (:external_id, :seller_id, :status, :start_at, :end_at, :reason, :created_by, :cancelled_at, :created_at, :updated_at)
        """)
        async with factory() as session:
            result = await session.execute(sql, params)
            await session.commit()
            new_id = result.lastrowid
        return await self.findById(str(new_id))

    async def update(
        self, id: str, update_data: Union[SellerAvailabilityInternalUpdate, Dict[str, Any]]
    ) -> Optional['SellerAvailability']:
        factory = self._get_session_factory()
        if not factory:
            return None
        now = datetime.now(timezone.utc)
        row_id = int(id) if str(id).isdigit() else id
        set_clauses = ["updated_at = :updated_at"]
        params: Dict[str, Any] = {"updated_at": now, "row_id": row_id}

        data_dict = (
            update_data.model_dump(exclude_unset=True, by_alias=False)
            if isinstance(update_data, SellerAvailabilityInternalUpdate)
            else dict(update_data)
        )

        for doc_field, col in self._COLUMN_MAP.items():
            if doc_field in data_dict:
                val = data_dict[doc_field]
                set_clauses.append(f"{col} = :{col}")
                if "_at" in doc_field and doc_field != "created_by":
                    params[col] = _to_dt(val)
                else:
                    params[col] = str(val) if val is not None else None

        sql = text(f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE id = :row_id")
        async with factory() as session:
            await session.execute(sql, params)
            await session.commit()
        return await self.findById(str(id))

    async def count(
        self,
        filters: Optional[Union[SellerAvailabilityFilter, Dict[str, Any]]] = None,
        seller_id: Optional[str] = None,
        status: Optional[Union[str, List[str]]] = None,
        id: Optional[Union[str, int]] = None,
    ) -> int:
        docs = await self.findAll(filters=filters, seller_id=seller_id, status=status, id=id)
        return len(docs)

    async def delete(self, id: str) -> bool:
        factory = self._get_session_factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(text(f"DELETE FROM {self.table_name} WHERE id = :id"), {"id": int(id)})
            await session.commit()
            return result.rowcount > 0
