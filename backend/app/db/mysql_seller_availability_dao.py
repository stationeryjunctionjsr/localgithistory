from app.models.daos_flat import SellerAvailabilityInternalCreate
import logging
"""
MySQL DAO for seller availability windows.
Fully normalized storage: no doc JSON.
Table: sj_seller_availability
"""

import secrets
from datetime import datetime, timezone
from typing import Dict
from app.models.seller_availability import SellerAvailability, List, Optional

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
        logging.warning("Background task failed", exc_info=e)
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

    def __map_to_schema(self, row) -> Any:
        return SellerAvailability.model_validate(dict(row._mapping))

    def _build_where(self, query: Dict):
        where_clauses = []
        params = {}
        for k, v in query.items():
            if k in ("_id", "id"):
                where_clauses.append("id = :q_id")
                params["q_id"] = int(v) if str(v).isdigit() else v
                continue
            col = self._COLUMN_MAP[k] if k in self._COLUMN_MAP else None
            p_name = f"qp_{k}"
            if col:
                if isinstance(v, dict) and "$in" in v:
                    phs = [f":{p_name}_{i}" for i, _ in enumerate(v["$in"])]
                    for i, item in enumerate(v["$in"]):
                        params[f"{p_name}_{i}"] = str(item)
                    where_clauses.append(f"{col} IN ({', '.join(phs)})" if phs else "1=0")
                else:
                    where_clauses.append(f"{col} = :{p_name}")
                    params[p_name] = str(v)
            else:
                pass  # Non-existent column, ignore
        return where_clauses, params

    async def findAll(self, query: Optional[Dict] = None) -> List[Any]:
        factory = self._get_session_factory()
        if not factory:
            return []
        where_clauses, params = self._build_where(query or {})
        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, seller_id, status, start_at, end_at, reason, created_by, cancelled_at, created_at, updated_at FROM {self.table_name}{where_sql} ORDER BY created_at DESC"
                ),
                params,
            )
            return [self.__map_to_schema(r) for r in result.fetchall()]

    async def findOne(self, query: Dict) -> Optional[Any]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Any]:
        return await self.findOne({"_id": id})

    async def create(self, data: SellerAvailabilityInternalCreate) -> Any:
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

    async def update(self, id: str, data: Dict) -> Optional[Any]:
        factory = self._get_session_factory()
        if not factory:
            return None
        now = datetime.now(timezone.utc)
        set_clauses = ["updated_at = :updated_at"]
        params: Dict = {"updated_at": now, "row_id": int(id) if str(id).isdigit() else id}

        for doc_field, col in self._COLUMN_MAP.items():
            if doc_field in data:
                set_clauses.append(f"{col} = :{col}")
                if "_at" in doc_field and doc_field != "created_by":
                    params[col] = _to_dt(data[doc_field])
                else:
                    params[col] = str(data[doc_field]) if data[doc_field] is not None else None

        sql = text(f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE id = :row_id")
        async with factory() as session:
            await session.execute(sql, params)
            await session.commit()
        return await self.findById(str(id))

    async def delete(self, id: str) -> bool:
        factory = self._get_session_factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(text(f"DELETE FROM {self.table_name} WHERE id = :id"), {"id": int(id)})
            await session.commit()
            return result.rowcount > 0
