"""
Generic Oracle document store for tables with (id, external_id, doc CLOB, created_at, updated_at).
Implements same interface as FileStorage for drop-in replacement.
Uses parameterized queries only.
"""

import json
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_doc(doc_clob: Optional[str]) -> dict:
    if not doc_clob:
        return {}
    try:
        return json.loads(doc_clob)
    except Exception:
        return {}


def _to_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


from app.config.settings import settings


class OracleDocStore:
    """
    Oracle-backed store for document-style tables.
    Table must have: id (NUMBER IDENTITY), external_id (VARCHAR2), doc/payload (CLOB), created_at, updated_at.
    """

    def __init__(self, table_name: str, doc_column: str = "doc"):
        self._raw_table_name = table_name
        self.doc_column = doc_column

    @property
    def table_name(self) -> str:
        suffix = getattr(settings, "table_suffix", "")
        return f"{self._raw_table_name}{suffix}"

    def _get_session_factory(self):
        return get_async_session_factory()

    def _row_to_doc(self, row) -> Dict:
        doc = _parse_doc(getattr(row, self.doc_column, None))
        doc["_db_id"] = str(row.id)
        if "_id" not in doc:
            doc["_id"] = str(row.id)
        doc["createdAt"] = row.created_at.isoformat() if row.created_at else _now_iso()
        doc["updatedAt"] = row.updated_at.isoformat() if row.updated_at else _now_iso()

        # Read from row.used_count if available and not present in doc
        if hasattr(row, "used_count") and row.used_count is not None:
            if "usedCount" not in doc:
                doc["usedCount"] = int(row.used_count)

        # Fallback to 0 if still not present
        if "usedCount" not in doc:
            doc["usedCount"] = 0

        return doc

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._get_session_factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    if str(v).isdigit():
                        # Numeric ID → match on the auto-increment primary key
                        where_clauses.append("id = :id")
                        params["id"] = int(v)
                    else:
                        # String ID (e.g. "system_retail_registered_no_order") → match
                        # against the _id field embedded in the JSON document
                        where_clauses.append(f"JSON_VALUE({self.doc_column}, '$._id') = :json_id")
                        params["json_id"] = str(v)
                elif v is not None:
                    param_name = f"qp_{k}"
                    where_clauses.append(f"JSON_VALUE({self.doc_column}, '$.{k}') = :{param_name}")
                    if isinstance(v, bool):
                        params[param_name] = "true" if v else "false"
                    else:
                        params[param_name] = str(v)

        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        cols = f"id, external_id, {self.doc_column}, created_at, updated_at"
        if self._raw_table_name == "sj_coupons":
            cols += ", used_count"

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT {cols} FROM {self.table_name}{where_sql} ORDER BY id ASC"), params
            )
            rows = result.fetchall()
            docs = []
            for r in rows:
                d = self._row_to_doc(r)
                if query:
                    match = True
                    for k, v in query.items():
                        if k in ("_id", "id"):
                            # Compare as strings but try to normalize
                            if str(d.get("_id")) != str(v):
                                match = False
                                break
                        elif d.get(k) != v:
                            match = False
                            break
                    if match:
                        docs.append(d)
                else:
                    docs.append(d)
            return docs

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def create(self, data: Dict) -> Dict:
        external_id = secrets.token_hex(16)
        now = datetime.now(timezone.utc)
        # Keep custom string _id if provided in data
        custom_id = data.get("_id")
        payload = {k: v for k, v in data.items() if k not in ("createdAt", "updatedAt")}
        if not custom_id or str(custom_id).isdigit():
            payload.pop("_id", None)
        doc_json = json.dumps(payload, default=str)
        factory = self._get_session_factory()
        if not factory:
            raise RuntimeError("Oracle not configured")

        cols = ["external_id", self.doc_column, "created_at", "updated_at"]
        vals = [":external_id", ":doc", ":created_at", ":updated_at"]
        params = {
            "external_id": external_id,
            "doc": doc_json,
            "created_at": now,
            "updated_at": now,
        }

        if self._raw_table_name == "sj_coupons":
            cols.append("used_count")
            vals.append(":used_count")
            params["used_count"] = int(data.get("usedCount") or 0)

            if "code" in data:
                cols.append("code")
                vals.append(":code")
                params["code"] = data.get("code")
            if "discountType" in data:
                cols.append("discount_type")
                vals.append(":discount_type")
                params["discount_type"] = data.get("discountType")
            if "discountValue" in data:
                cols.append("discount_value")
                vals.append(":discount_value")
                params["discount_value"] = float(data.get("discountValue") or 0)
            if "minPurchaseAmount" in data:
                cols.append("min_order_value")
                vals.append(":min_order_value")
                params["min_order_value"] = float(data.get("minPurchaseAmount") or 0)
            if "usageLimit" in data:
                cols.append("max_uses")
                vals.append(":max_uses")
                params["max_uses"] = int(data.get("usageLimit")) if data.get("usageLimit") is not None else None
            if "isActive" in data:
                cols.append("is_active")
                vals.append(":is_active")
                params["is_active"] = 1 if data.get("isActive") else 0
            if "validFrom" in data:
                cols.append("start_date")
                vals.append(":start_date")
                params["start_date"] = _to_datetime(data.get("validFrom"))
            if "validUntil" in data:
                cols.append("end_date")
                vals.append(":end_date")
                params["end_date"] = _to_datetime(data.get("validUntil"))

        cols_str = ", ".join(cols)
        vals_str = ", ".join(vals)

        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    INSERT INTO {self.table_name} ({cols_str})
                    VALUES ({vals_str})
                    RETURNING id INTO :out_id
                    """
                ),
                {**params, "out_id": 0},
            )
            # SQLAlchemy RETURNING handling depends on DB driver (cx_Oracle usually returns as list or via cursor)
            # Alternatively, fetch lastval if RETURNING is complex in this setup
            await session.commit()

            # Refetch to get the actual auto-increment ID
            result = await session.execute(
                text(f"SELECT id FROM {self.table_name} WHERE external_id = :eid"), {"eid": external_id}
            )
            new_id = result.scalar()

        out = dict(data)
        out["_id"] = str(custom_id) if custom_id and not str(custom_id).isdigit() else str(new_id)
        out["_db_id"] = str(new_id)
        out["createdAt"] = now.isoformat()
        out["updatedAt"] = now.isoformat()
        return out

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        db_id = existing.get("_db_id") or id
        factory = self._get_session_factory()
        if not factory:
            return None

        cols = f"id, external_id, {self.doc_column}, created_at, updated_at"
        if self._raw_table_name == "sj_coupons":
            cols += ", used_count"

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT {cols} FROM {self.table_name} WHERE id = :id"),
                {"id": int(db_id) if str(db_id).isdigit() else 0},
            )
            row = result.fetchone()
            if not row:
                return None
            doc = _parse_doc(getattr(row, self.doc_column, None))
            doc.update(update_data)
            if "_id" in existing and not str(existing["_id"]).isdigit():
                doc["_id"] = existing["_id"]
            else:
                doc.pop("_id", None)
            doc.pop("_db_id", None)
            doc.pop("createdAt", None)
            now = datetime.now(timezone.utc)
            doc["updatedAt"] = now.isoformat()
            doc_json = json.dumps(doc, default=str)

            update_sql = f"SET {self.doc_column} = :doc, updated_at = :updated_at"
            params = {"doc": doc_json, "updated_at": now, "id": int(db_id)}

            if self._raw_table_name == "sj_coupons":
                if "usedCount" in update_data:
                    update_sql += ", used_count = :used_count"
                    params["used_count"] = int(update_data["usedCount"])
                if "code" in update_data:
                    update_sql += ", code = :code"
                    params["code"] = update_data["code"]
                if "discountType" in update_data:
                    update_sql += ", discount_type = :discount_type"
                    params["discount_type"] = update_data["discountType"]
                if "discountValue" in update_data:
                    update_sql += ", discount_value = :discount_value"
                    params["discount_value"] = float(update_data["discountValue"])
                if "minPurchaseAmount" in update_data:
                    update_sql += ", min_order_value = :min_order_value"
                    params["min_order_value"] = float(update_data["minPurchaseAmount"])
                if "usageLimit" in update_data:
                    update_sql += ", max_uses = :max_uses"
                    params["max_uses"] = (
                        int(update_data["usageLimit"]) if update_data["usageLimit"] is not None else None
                    )
                if "isActive" in update_data:
                    update_sql += ", is_active = :is_active"
                    params["is_active"] = 1 if update_data["isActive"] else 0
                if "validFrom" in update_data:
                    update_sql += ", start_date = :start_date"
                    params["start_date"] = _to_datetime(update_data["validFrom"])
                if "validUntil" in update_data:
                    update_sql += ", end_date = :end_date"
                    params["end_date"] = _to_datetime(update_data["validUntil"])

            await session.execute(
                text(f"UPDATE {self.table_name} {update_sql} WHERE id = :id"),
                params,
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        existing = await self.findById(id)
        if not existing:
            return False
        db_id = existing.get("_db_id") or id
        factory = self._get_session_factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.table_name} WHERE id = :id"),
                {"id": int(db_id) if str(db_id).isdigit() else 0},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            eid = d.get("_id")
            if eid and await self.delete(eid):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)

    find_all = findAll
    find_by_id = findById
    find_one = findOne
