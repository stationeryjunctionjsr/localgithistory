"""
MySQL DAO for referral settings: one row per segment (retail / business), typed columns.
Maps settings schema: ReferralSettings(id, retail=ReferralSegment, business=ReferralSegment).
"""

from typing import List, Optional
from app.models.referral_settings import ReferralSettings, ReferralSegment

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc

SEGMENTS = ("retail", "business")


def _row_to_segment(r) -> ReferralSegment:
    return ReferralSegment(
        segment=r.segment,
        discount_type=r.discount_type or "percentage",
        discount_value=float(r.discount_value) if r.discount_value is not None else 0.0,
        is_active=bool(r.is_active) if r.is_active is not None else False,
    )


class MySQLReferralSettingsDAO:
    @property
    def TABLE(self) -> str:
        return "sj_referral_settings"

    def _factory(self):
        return get_async_session_factory()

    def _map_to_schema(self, retail_row, business_row) -> ReferralSettings:
        return ReferralSettings(
            id="1",
            retail=_row_to_segment(retail_row) if retail_row else ReferralSegment(segment="retail", discount_type="percentage", discount_value=0.0, is_active=False),
            business=_row_to_segment(business_row) if business_row else ReferralSegment(segment="business", discount_type="percentage", discount_value=0.0, is_active=False),
        )

    async def findAll(self) -> List[ReferralSettings]:
        settings_data = await self._get_settings()
        return [settings_data] if settings_data else []

    async def findById(self, id: str) -> Optional[ReferralSettings]:
        return await self._get_settings()

    async def findOne(self) -> Optional[ReferralSettings]:
        return await self._get_settings()

    async def _get_settings(self) -> Optional[ReferralSettings]:
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
        retail_row = None
        business_row = None
        for r in rows:
            if r.segment == "retail":
                retail_row = r
            elif r.segment == "business":
                business_row = r
        return self._map_to_schema(retail_row, business_row)

    async def create(self, data: ReferralSettings) -> Optional[ReferralSettings]:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        async with factory() as session:
            for seg in SEGMENTS:
                obj = data.retail if seg == "retail" else data.business
                if not obj:
                    discount_type = "percentage"
                    discount_value = 0.0
                    is_active = 0
                else:
                    discount_type = obj.discount_type or "percentage"
                    discount_value = float(obj.discount_value) if obj.discount_value is not None else 0.0
                    is_active = 1 if obj.is_active else 0
                await session.execute(
                    text(
                        f"""
                        INSERT INTO {self.TABLE} (segment, discount_type, discount_value, is_active, created_at, updated_at)
                        VALUES (:segment, :discount_type, :discount_value, :is_active, :created_at, :updated_at)
                        """
                    ),
                    {
                        "segment": seg,
                        "discount_type": discount_type,
                        "discount_value": discount_value,
                        "is_active": is_active,
                        "created_at": now,
                        "updated_at": now,
                    },
                )
            await session.commit()
        return await self._get_settings()

    async def update(self, id: str, update_data: ReferralSettings) -> Optional[ReferralSettings]:
        factory = self._factory()
        if not factory:
            return None
        now = now_utc()
        for seg in SEGMENTS:
            obj = update_data.retail if seg == "retail" else update_data.business
            if obj is None:
                continue
            discount_type = obj.discount_type or "percentage"
            discount_value = float(obj.discount_value) if obj.discount_value is not None else 0.0
            is_active = 1 if obj.is_active else 0
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
                            INSERT INTO {self.TABLE} (segment, discount_type, discount_value, is_active, created_at, updated_at)
                            VALUES (:segment, :discount_type, :discount_value, :is_active, :created_at, :updated_at)
                            """
                        ),
                        {
                            "segment": seg,
                            "discount_type": discount_type,
                            "discount_value": discount_value,
                            "is_active": is_active,
                            "created_at": now,
                            "updated_at": now,
                        },
                    )
                await session.commit()
        return await self._get_settings()

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(text(f"DELETE FROM {self.TABLE}"))
            await session.commit()
            return result.rowcount > 0

    async def count(self) -> int:
        settings_data = await self._get_settings()
        return 1 if settings_data else 0

    find_all = findAll
    find_by_id = findById
    find_one = findOne
