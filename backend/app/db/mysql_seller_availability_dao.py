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
    except Exception:
        return None


class MySQLSellerAvailabilityDAO:
    _COLUMN_MAP = {
        "sellerId": "seller_id",
        "status": "status",
        "startAt": "start_at",
        "endAt": "end_at",
        "reason": "reason",
        "createdBy": "created_by",
        "cancelledAt": "cancelled_at",
    }

    @property
    def table_name(self) -> str:
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_seller_availability{suffix}"

    def _get_session_factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, row) -> Dict:
        doc = {
            "_id": str(row.id),
            "_db_id": str(row.id),
        }
        if row.seller_id:
            doc["sellerId"] = row.seller_id
        if row.status:
            doc["status"] = row.status
        if row.start_at:
            doc["startAt"] = row.start_at.isoformat()
        if row.end_at:
            doc["endAt"] = row.end_at.isoformat()
        if row.reason:
            doc["reason"] = row.reason
        if row.created_by:
            doc["createdBy"] = row.created_by
        if row.cancelled_at:
            doc["cancelledAt"] = row.cancelled_at.isoformat()

        doc["createdAt"] = row.created_at.isoformat() if row.created_at else _now_iso()
        doc["updatedAt"] = row.updated_at.isoformat() if row.updated_at else _now_iso()
        return doc

    def _build_where(self, query: Dict):
        where_clauses = []
        params = {}
        for k, v in query.items():
            if k in ("_id", "id"):
                where_clauses.append("id = :q_id")
                params["q_id"] = int(v) if str(v).isdigit() else v
                continue
            col = self._COLUMN_MAP.get(k)
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

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
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
            return [self._row_to_dict(r) for r in result.fetchall()]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def create(self, data: Dict) -> Dict:
        factory = self._get_session_factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = datetime.now(timezone.utc)
        params = {
            "external_id": secrets.token_hex(16),
            "seller_id": str(data.sellerId or ""),
            "status": (data.status if getattr(data, 'status', None) is not None else "scheduled"),
            "start_at": _to_dt(data.startAt),
            "end_at": _to_dt(data.endAt),
            "reason": data.reason,
            "created_by": data.createdBy,
            "cancelled_at": _to_dt(data.cancelledAt),
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
        created = dict(data)
        created["_id"] = str(new_id)
        created["createdAt"] = now.isoformat()
        created["updatedAt"] = now.isoformat()
        return created

    async def update(self, id: str, data: Dict) -> Optional[Dict]:
        factory = self._get_session_factory()
        if not factory:
            return None
        now = datetime.now(timezone.utc)
        set_clauses = ["updated_at = :updated_at"]
        params: Dict = {"updated_at": now, "row_id": int(id) if str(id).isdigit() else id}

        for doc_field, col in self._COLUMN_MAP.items():
            if doc_field in data:
                set_clauses.append(f"{col} = :{col}")
                if "At" in doc_field and doc_field != "createdBy":
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
