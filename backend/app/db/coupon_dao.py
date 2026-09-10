"""
Oracle DAO for sj_coupons. Implements FileStorage-like interface for 'coupons'.
"""

from app.config.settings import settings
import secrets
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.oracle_utils import now_utc


def _to_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


class OracleCouponDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_coupons{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_dict(self, r) -> Dict:
        return {
            "_id": str(r.id),
            "code": r.code,
            "discountType": r.discount_type,
            "discountValue": float(r.discount_value) if r.discount_value is not None else None,
            "minOrderValue": float(r.min_order_value) if r.min_order_value is not None else None,
            "maxUses": int(r.max_uses) if r.max_uses is not None else None,
            "usedCount": int(r.used_count) if r.used_count is not None else 0,
            "startDate": r.start_date.isoformat() if r.start_date else None,
            "endDate": r.end_date.isoformat() if r.end_date else None,
            "isActive": bool(r.is_active) if r.is_active is not None else True,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
        }

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id, external_id, code, discount_type, discount_value, min_order_value, max_uses,
                           used_count, start_date, end_date, is_active, created_at, updated_at
                    FROM {self.TABLE}
                    """
                )
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
                    f"""
                    SELECT id, external_id, code, discount_type, discount_value, min_order_value, max_uses,
                           used_count, start_date, end_date, is_active, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
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
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self.TABLE} (
                        external_id, code, discount_type, discount_value, min_order_value, max_uses,
                        used_count, start_date, end_date, is_active, created_at, updated_at
                    ) VALUES (
                        :external_id, :code, :discount_type, :discount_value, :min_order_value, :max_uses,
                        :used_count, :start_date, :end_date, :is_active, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "external_id": external_id,
                    "code": data.get("code"),
                    "discount_type": data.get("discountType"),
                    "discount_value": data.get("discountValue"),
                    "min_order_value": data.get("minOrderValue"),
                    "max_uses": data.get("maxUses"),
                    "used_count": data.get("usedCount", 0),
                    "start_date": _to_ts(data.get("startDate")),
                    "end_date": _to_ts(data.get("endDate")),
                    "is_active": 1 if data.get("isActive", True) else 0,
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
        async with factory() as session:
            await session.execute(
                text(
                    f"""
                    UPDATE {self.TABLE} SET
                        code = :code,
                        discount_type = :discount_type,
                        discount_value = :discount_value,
                        min_order_value = :min_order_value,
                        max_uses = :max_uses,
                        used_count = :used_count,
                        start_date = :start_date,
                        end_date = :end_date,
                        is_active = :is_active,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": cid,
                    "code": merged.get("code"),
                    "discount_type": merged.get("discountType"),
                    "discount_value": merged.get("discountValue"),
                    "min_order_value": merged.get("minOrderValue"),
                    "max_uses": merged.get("maxUses"),
                    "used_count": merged.get("usedCount", 0),
                    "start_date": _to_ts(merged.get("startDate")),
                    "end_date": _to_ts(merged.get("endDate")),
                    "is_active": 1 if merged.get("isActive", True) else 0,
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
