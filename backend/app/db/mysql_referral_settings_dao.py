"""
MySQL DAO for referral settings: one row per segment (retail / business), typed columns.
Exposes single virtual doc: { _id, retail: { segment, discountType, discountValue, isActive }, business: {...} }.
"""

from typing import Any
import secrets
from typing import Dict
from app.models.referral_settings import ReferralSettings, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc

SEGMENTS = ("retail", "business")


def _row_to_segment(r) -> Dict:
    return {
        "segment": r.segment,
        "discount_type": r.discount_type or "percentage",
        "discount_value": float(r.discount_value) if r.discount_value is not None else 0,
        "is_active": bool(r.is_active) if r.is_active is not None else False,
    }


class MySQLReferralSettingsDAO:
    @property
    def TABLE(self) -> str:
        return "sj_referral_settings"

    def _factory(self):
        return get_async_session_factory()

    def _doc(self, rows_by_segment: Dict[str, any]) -> Any:
        retail = (rows_by_segment["retail"] if "retail" in rows_by_segment else None)
        business = (rows_by_segment["business"] if "business" in rows_by_segment else None)
        return ReferralSettings.model_validate({
            "_id": "1",
            "retail": _row_to_segment(retail)
            if retail
            else {"segment": "retail", "discount_type": "percentage", "discount_value": 0, "is_active": False},
            "business": _row_to_segment(business)
            if business
            else {"segment": "business", "discount_type": "percentage", "discount_value": 0, "is_active": False},
        })

    async def findAll(self, query: Optional[Dict] = None) -> List[Dict]:
        doc = await self._get_settings_doc()
        return [doc] if doc else []

    async def findById(self, id: str) -> Optional[Dict]:
        return await self._get_settings_doc()

    async def findOne(self, query: Dict) -> Optional[Dict]:
        return await self._get_settings_doc()

    async def _get_settings_doc(self) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT id, segment, discount_type, discount_value, is_active FROM {self.TABLE}")
            )
            rows = result.fetchall()
        if not rows:
            return None
        Row = type("Row", (), {})
        by_segment = {}
        for r in rows:
            row = Row()
            row.id = r[0]
            row.segment = r[1]
            row.discount_type = r[2]
            row.discount_value = r[3]
            row.is_active = r[4]
            by_segment[row.segment] = row
        return self._doc(by_segment)

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        defaults = {"segment": "retail", "discount_type": "percentage", "discount_value": 0, "is_active": False}
        async with factory() as session:
            for seg in SEGMENTS:
                obj = getattr(data, seg, None) if hasattr(data, seg) else data.get(seg)
                if not obj:
                    obj = {**defaults, "segment": seg}
                discount_type = (obj.discount_type if hasattr(obj, "discount_type") else obj.get("discount_type")) or "percentage"
                discount_value = (
                    (obj.discount_value if hasattr(obj, "discount_value") else None) if (obj.discount_value if hasattr(obj, "discount_value") else None) is not None else (obj.discount_value if hasattr(obj, "discount_value") else 0)
                )
                is_active = 1 if (obj.is_active if hasattr(obj, "is_active") else obj.get("is_active")) else 0
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self.TABLE} (external_id, segment, discount_type, discount_value, is_active, created_at, updated_at)
                        VALUES (:external_id, :segment, :discount_type, :discount_value, :is_active, :created_at, :updated_at)
                        """
                    ),
                    {
                        "external_id": secrets.token_hex(16),
                        "segment": seg,
                        "discount_type": discount_type,
                        "discount_value": discount_value,
                        "is_active": is_active,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
            await session.commit()
        return await self._get_settings_doc()

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        for seg in SEGMENTS:
            obj = getattr(update_data, seg, None) if hasattr(update_data, seg) else update_data.get(seg)
            if obj is None:
                continue
            discount_type = (obj.discount_type if hasattr(obj, "discount_type") else obj.get("discount_type")) or "percentage"
            discount_value = (
                (obj.discount_value if hasattr(obj, "discount_value") else None) if (obj.discount_value if hasattr(obj, "discount_value") else None) is not None else (obj.discount_value if hasattr(obj, "discount_value") else 0)
            )
            is_active = 1 if (obj.is_active if hasattr(obj, "is_active") else obj.get("is_active")) else 0
            async with factory() as session:
                result = await session.execute(
                    text(
                        f"""
                        UPDATE {self.TABLE} SET discount_type = :discount_type, discount_value = :discount_value, is_active = :is_active, updated_at = :updated_at
                        WHERE segment = :segment
                        """
                    ),
                    {
                        "segment": seg,
                        "discount_type": discount_type,
                        "discount_value": discount_value,
                        "is_active": is_active,
                        "updated_at": now,
                    },
                )
                if result.rowcount == 0:
                    await session.execute(
                        text(
                            f"""
                            INSERT INTO {self.TABLE} (external_id, segment, discount_type, discount_value, is_active, created_at, updated_at)
                            VALUES (:external_id, :segment, :discount_type, :discount_value, :is_active, :created_at, :updated_at)
                            """
                        ),
                        {
                            "external_id": secrets.token_hex(16),
                            "segment": seg,
                            "discount_type": discount_type,
                            "discount_value": discount_value,
                            "is_active": is_active,
                            "created_at": now,
                            "updated_at": now,
                        },
                    )
                await session.commit()
        return await self._get_settings_doc()

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(text(f"DELETE FROM {self.TABLE}"))
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Dict:
        n = await self.delete("1")
        return {"deletedCount": 1 if n else 0}

    async def count(self, query: Optional[Dict] = None) -> int:
        doc = await self._get_settings_doc()
        return 1 if doc else 0

    find_all = findAll
    find_by_id = findById
    find_one = findOne
