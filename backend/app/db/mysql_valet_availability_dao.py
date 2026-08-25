"""
MySQL DAO for sj_valet_availability (Relational).
"""

import secrets
from typing import Dict, List, Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.config.settings import settings
from app.db.oracle_utils import now_utc


class MySQLValetAvailabilityDAO:
    @property
    def TABLE(self):
        suffix = getattr(settings, "table_suffix", "")
        return f"sj_valet_availability{suffix}"

    def _factory(self):
        return get_async_session_factory()

    def _row_to_doc(self, r, children: Dict) -> Dict:
        return {
            "_id": str(r.id),
            "externalId": r.external_id,
            "date": r.date.isoformat() if hasattr(r.date, "isoformat") else str(r.date),
            "availabilityType": r.availability_type,
            "slots": children.get("slots", []),
            "zones": children.get("zones", []),
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
                elif k == "date":
                    where_clauses.append("date = :date")
                    params["date"] = str(v)
                elif k == "availabilityType":
                    where_clauses.append("availability_type = :atype")
                    params["atype"] = str(v)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, external_id, date, availability_type, created_at, updated_at FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"
                ),
                params,
            )
            rows = result.fetchall()

            children_map = {r.id: {"slots": [], "zones": []} for r in rows}
            if rows:
                ids = [r.id for r in rows]
                chunks = [ids[i : i + 999] for i in range(0, len(ids), 999)]
                for chunk in chunks:
                    chunk_params = {f"id_{i}": cid for i, cid in enumerate(chunk)}
                    placeholders = ", ".join([f":{k}" for k in chunk_params.keys()])

                    s_res = await session.execute(
                        text(
                            f"SELECT availability_id, slot FROM sj_valet_availability_slots WHERE availability_id IN ({placeholders}) ORDER BY id ASC"
                        ),
                        chunk_params,
                    )
                    for sr in s_res.fetchall():
                        children_map[sr.availability_id]["slots"].append(sr.slot)

                    z_res = await session.execute(
                        text(
                            f"SELECT availability_id, zone FROM sj_valet_availability_zones WHERE availability_id IN ({placeholders}) ORDER BY id ASC"
                        ),
                        chunk_params,
                    )
                    for zr in z_res.fetchall():
                        children_map[zr.availability_id]["zones"].append(zr.zone)

        return [self._row_to_doc(r, children_map[r.id]) for r in rows]

    async def findOne(self, query: Dict) -> Optional[Dict]:
        docs = await self.findAll(query)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[Dict]:
        return await self.findOne({"_id": id})

    async def _replace_children(self, session, availability_id: int, data: Dict):
        await session.execute(
            text("DELETE FROM sj_valet_availability_slots WHERE availability_id = :aid"), {"aid": availability_id}
        )
        await session.execute(
            text("DELETE FROM sj_valet_availability_zones WHERE availability_id = :aid"), {"aid": availability_id}
        )

        for s in data.get("slots", []):
            await session.execute(
                text("INSERT INTO sj_valet_availability_slots (availability_id, slot) VALUES (:aid, :s)"),
                {"aid": availability_id, "s": s},
            )

        for z in data.get("zones", []):
            await session.execute(
                text("INSERT INTO sj_valet_availability_zones (availability_id, zone) VALUES (:aid, :z)"),
                {"aid": availability_id, "z": z},
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
                    INSERT INTO {self.TABLE} (external_id, date, availability_type, created_at, updated_at) 
                    VALUES (:external_id, :date, :availability_type, :created_at, :updated_at)
                """),
                {
                    "external_id": external_id,
                    "date": data.get("date"),
                    "availability_type": data.get("availabilityType", ""),
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

    async def update(self, id: str, update_data: Dict) -> Optional[Dict]:
        existing = await self.findById(id)
        if not existing:
            return None
        merged = {**existing, **update_data}
        now = now_utc()
        factory = self._factory()

        async with factory() as session:
            await session.execute(
                text(
                    f"UPDATE {self.TABLE} SET date = :date, availability_type = :atype, updated_at = :upd WHERE id = :id"
                ),
                {
                    "id": int(id) if str(id).isdigit() else 0,
                    "date": merged.get("date"),
                    "atype": merged.get("availabilityType", ""),
                    "upd": now,
                },
            )
            await self._replace_children(session, int(id) if str(id).isdigit() else 0, merged)
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": int(id) if str(id).isdigit() else 0}
            )
            await session.commit()
            return result.rowcount > 0
