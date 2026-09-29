"""
MySQL DAO for sj_commission_settings (Relational).
"""

import secrets
from typing import List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.commission_settings import (
    CommissionSettings,
    CommissionSettingsInternalCreate,
    CommissionSettingsInternalUpdate,
    CommissionTierInternal
)

class MySQLCommissionSettingsDAO:
    TABLE = "sj_commission_settings"

    def _factory(self):
        return get_async_session_factory()

    async def findAll(self) -> List[CommissionSettings]:
        factory = self._factory()
        if not factory:
            return []

        async with factory() as session:
            result = await session.execute(
                text(f"SELECT id, external_id, default_commission_pct, created_at, updated_at FROM {self.TABLE} ORDER BY id ASC")
            )
            rows = result.fetchall()

            children_map = {str(r.id): [] for r in rows}
            if rows:
                ids = [r.id for r in rows]
                chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
                for chunk in chunks:
                    chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
                    placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])
                    t_res = await session.execute(
                        text(
                            f"SELECT setting_id, min_val, max_val, commission_pct FROM sj_commission_settings_tiers WHERE setting_id IN ({placeholders}) ORDER BY id ASC"
                        ),
                        chunk_params,
                    )
                    for tr in t_res.fetchall():
                        children_map[str(tr.setting_id)].append(
                            CommissionTierInternal(
                                min=float(tr.min_val) if tr.min_val is not None else None,
                                max=float(tr.max_val) if tr.max_val is not None else None,
                                pct=float(tr.commission_pct) if tr.commission_pct is not None else 0.0,
                            )
                        )

        out = []
        for r in rows:
            out.append(CommissionSettings(
                id=str(r.id),
                external_id=r.external_id,
                default_commission_pct=float(r.default_commission_pct) if r.default_commission_pct is not None else 5.0,
                created_at=r.created_at,
                updated_at=r.updated_at,
                tiers=children_map[str(r.id)]
            ))
        return out

    async def findById(self, id: str) -> Optional[CommissionSettings]:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT id, external_id, default_commission_pct, created_at, updated_at FROM {self.TABLE} WHERE id = :id"),
                {"id": pid}
            )
            r = result.fetchone()
            if not r:
                return None
                
            t_res = await session.execute(
                text("SELECT min_val, max_val, commission_pct FROM sj_commission_settings_tiers WHERE setting_id = :sid ORDER BY id ASC"),
                {"sid": pid}
            )
            tiers = [
                CommissionTierInternal(
                    min=float(tr.min_val) if tr.min_val is not None else None,
                    max=float(tr.max_val) if tr.max_val is not None else None,
                    pct=float(tr.commission_pct) if tr.commission_pct is not None else 0.0,
                )
                for tr in t_res.fetchall()
            ]
            
            return CommissionSettings(
                id=str(r.id),
                external_id=r.external_id,
                default_commission_pct=float(r.default_commission_pct) if r.default_commission_pct is not None else 5.0,
                created_at=r.created_at,
                updated_at=r.updated_at,
                tiers=tiers
            )

    async def _replace_children(self, session, setting_id: int, tiers: List[CommissionTierInternal]):
        await session.execute(
            text("DELETE FROM sj_commission_settings_tiers WHERE setting_id = :sid"), {"sid": setting_id}
        )
        for t in tiers:
            await session.execute(
                text(
                    "INSERT INTO sj_commission_settings_tiers (setting_id, min_val, max_val, commission_pct) VALUES (:sid, :minv, :maxv, :pct)"
                ),
                {
                    "sid": setting_id, 
                    "minv": t.min,
                    "maxv": t.max,
                    "pct": t.pct
                },
            )

    async def create(self, data: CommissionSettingsInternalCreate) -> CommissionSettings:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)

        async with factory() as session:
            await session.execute(
                text(f"""
                    INSERT INTO {self.TABLE} (external_id, default_commission_pct, created_at, updated_at) 
                    VALUES (:external_id, :default_commission_pct, :created_at, :updated_at)
                """),
                {
                    "external_id": external_id,
                    "default_commission_pct": data.default_commission_pct,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data.tiers)
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: CommissionSettingsInternalUpdate) -> Optional[CommissionSettings]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        now = now_utc()
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None

        pct = existing.default_commission_pct
        if update_data.default_commission_pct is not None:
            pct = update_data.default_commission_pct

        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET default_commission_pct = :pct, updated_at = :upd WHERE id = :id"),
                {"id": pid, "pct": pct, "upd": now},
            )
            if update_data.tiers is not None:
                await self._replace_children(session, pid, update_data.tiers)
            await session.commit()
            
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        pid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pid}
            )
            await session.commit()
            return result.rowcount > 0
