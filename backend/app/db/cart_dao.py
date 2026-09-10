"""
Oracle DAO for sj_carts. Implements FileStorage-like interface for 'carts'.
"""

from app.config.settings import settings
import secrets
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.oracle_utils import json_dumps, json_loads, now_utc


class OracleCartDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_carts{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, r) -> Dict:
        return {
            "_id": str(r.id),
            "user": str(r.user_id),
            "items": json_loads(r.items) or [],
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else 0
                elif k in ("user", "user_id"):
                    where_clauses.append("user_id = :user_id")
                    params["user_id"] = int(v) if str(v).isdigit() else 0
                elif k == "external_id":
                    where_clauses.append("external_id = :external_id")
                    params["external_id"] = str(v)

        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT id, external_id, user_id, items, created_at, updated_at FROM {self.TABLE}{where_sql}"),
                params,
            )
            rows = result.fetchall()
        docs = [self._row_to_dict(r) for r in rows]
        if not query:
            return docs
        filtered: List[Dict] = []
        for d in docs:
            match = True
            for k, v in query.items():
                if k in ("_id", "id"):
                    if str(d.get("_id")) != str(v):
                        match = False
                        break
                elif k in ("user", "user_id"):
                    if str(d.get("user")) != str(v):
                        match = False
                        break
                elif d.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(d)
        return filtered

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        cid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, external_id, user_id, items, created_at, updated_at FROM {self.TABLE} WHERE id = :id"
                ),
                {"id": cid},
            )
            row = result.fetchone()
        return self._row_to_dict(row) if row else None

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("Oracle not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)
        user_id = int(data.get("user")) if str(data.get("user", "")).isdigit() else None
        if user_id is None:
            raise ValueError("Cart user must be numeric id when using Oracle")

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (external_id, user_id, items, created_at, updated_at)
                    VALUES (:external_id, :user_id, :items, :created_at, :updated_at)
                    """
                ),
                {
                    "external_id": external_id,
                    "user_id": user_id,
                    "items": json_dumps(data.get("items") or []),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await session.commit()
            r = await session.execute(
                text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"),
                {"eid": external_id},
            )
            new_id = r.scalar()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        cid = int(id) if str(id).isdigit() else 0
        user_id = int(merged.get("user")) if str(merged.get("user", "")).isdigit() else None
        if user_id is None:
            return None

        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE}
                    SET user_id = :user_id, items = :items, updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": cid,
                    "user_id": user_id,
                    "items": json_dumps(merged.get("items") or []),
                    "updated_at": now,
                },
            )
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        cid = int(id) if str(id).isdigit() else 0
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": cid},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            if await self.delete(d.get("_id")):
                deleted += 1
        return {"deletedCount": deleted}

    async def count(self, query: Optional[Dict] = None) -> int:
        docs = await self.findAll(query)
        return len(docs)

    find_all = findAll
    find_by_id = findById
    find_one = findOne
