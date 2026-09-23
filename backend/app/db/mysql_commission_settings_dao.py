from typing import Any
"""
MySQL DAO for sj_commission_settings (Relational).
"""

import secrets
from typing import Dict
from app.models.commission_settings import CommissionSettings, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.db_utils import now_utc


class MySQLCommissionSettingsDAO:
    @property
    def TABLE(self):
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"sj_commission_settings{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def __map_to_schema(self, r, tiers: List[Dict]) -> Dict:
        return {
            "_id": str(r.id),
            "externalId": r.external_id,
            "defaultCommissionPct": float(r.default_commission_pct) if r.default_commission_pct is not None else 0.0,
            "tiers": tiers,
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
                    params["id"] = int(v) if str(v).isdigit() else None

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, external_id, default_commission_pct, created_at, updated_at FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"
                ),
                params,
            )
            rows = result.fetchall()

            children_map = {r.id: [] for r in rows}
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
                        children_map[tr.setting_id].append(
                            {
                                "min": float(tr.min_val) if tr.min_val is not None else None,
                                "max": float(tr.max_val) if tr.max_val is not None else None,
                                "pct": float(tr.commission_pct) if tr.commission_pct is not None else None,
                            }
                        )

        return [CommissionSettings.model_validate(self.__map_to_schema(r, children_map[r.id]) ) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def _replace_children(self, session, setting_id: int, data: Dict):
        await session.execute(
            text("DELETE FROM sj_commission_settings_tiers WHERE setting_id = :sid"), {"sid": setting_id}
        )
        for t in (data.tiers if data.tiers is not None else []):
            await session.execute(
                text(
                    "INSERT INTO sj_commission_settings_tiers (setting_id, min_val, max_val, commission_pct) VALUES (:sid, :minv, :maxv, :pct)"
                ),
                {"sid": setting_id, "minv": (t["min"] if "min" in t else None), "maxv": (t["max"] if "max" in t else None), "pct": (t["pct"] if "pct" in t else 0)},
            )

    async def create(self, data: Dict) -> Dict:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
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
                    "default_commission_pct": (data.defaultCommissionPct if data.defaultCommissionPct is not None else 5.0),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: Any) -> Optional[Any]:
        existing = await self.findById(id)
        if not existing:
            return None
            
        pct = existing.default_commission_pct
        if update_data.defaultCommissionPct is not None:
            pct = update_data.defaultCommissionPct
            
        now = now_utc()
        factory = self._factory()

        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET default_commission_pct = :pct, updated_at = :upd WHERE id = :id"),
                {"id": int(id) if str(id).isdigit() else None, "pct": pct if pct is not None else 5.0, "upd": now},
            )
            if update_data.categories is not None or update_data.brands is not None or update_data.products is not None:
                # Merge existing and new child arrays securely without dictionary unpacking
                merged_data = type("Merged", (object,), {})()
                merged_data.categories = update_data.categories if update_data.categories is not None else existing.categories
                merged_data.brands = update_data.brands if update_data.brands is not None else existing.brands
                merged_data.products = update_data.products if update_data.products is not None else existing.products
                await self._replace_children(session, int(id) if str(id).isdigit() else None, merged_data)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else None}
            )
            await session.commit()
            return result.rowcount > 0
