"""
MySQL DAO for sj_valet_availability (Relational).
"""

import secrets
from datetime import date, datetime
from typing import Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.daos import (
    ValetAvailabilityFilter,
    ValetAvailabilityInternalCreate,
    ValetAvailabilityInternalUpdate,
)
from app.models.valet_availability import ValetAvailability


def _format_date(d: Optional[date | datetime | str]) -> Optional[str]:
    if d is None:
        return None
    if isinstance(d, (datetime, date)):
        return d.strftime("%Y-%m-%d")
    return str(d)


def _map_row(r, children_slots: list[str], children_zones: list[str]) -> ValetAvailability:
    return ValetAvailability(
        id=str(r.id),
        external_id=r.external_id,
        valet_id=r.valet_id,
        date=_format_date(r.date),
        availability_type=r.availability_type,
        slots=children_slots,
        zones=children_zones,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


class MySQLValetAvailabilityDAO:
    @property
    def TABLE(self) -> str:
        return "sj_valet_availability"

    def _factory(self):
        return get_async_session_factory()

    async def findAll(
        self, filters: Optional[ValetAvailabilityFilter] = None
    ) -> list[ValetAvailability]:
        factory = self._factory()
        if not factory:
            return []

        where_clauses: list[str] = []
        params: dict[str, object] = {}

        if filters is not None:
            if filters.id is not None:
                where_clauses.append("id = :id")
                params["id"] = int(filters.id) if str(filters.id).isdigit() else str(filters.id)
            if filters.valet_id is not None:
                where_clauses.append("valet_id = :valet_id")
                params["valet_id"] = str(filters.valet_id)
            if filters.date is not None:
                where_clauses.append("date = :date")
                params["date"] = str(filters.date)
            if filters.availability_type is not None:
                where_clauses.append("availability_type = :atype")
                params["atype"] = str(filters.availability_type)
            if filters.start_date is not None:
                where_clauses.append("date >= :start_date")
                params["start_date"] = str(filters.start_date)
            if filters.end_date is not None:
                where_clauses.append("date <= :end_date")
                params["end_date"] = str(filters.end_date)
            if filters.seller_zones is not None and len(filters.seller_zones) > 0:
                phs = [f":sz_{i}" for i in range(len(filters.seller_zones))]
                for i, sz in enumerate(filters.seller_zones):
                    params[f"sz_{i}"] = str(sz)
                where_clauses.append(
                    f"EXISTS (SELECT 1 FROM sj_valet_availability_zones vaz WHERE vaz.availability_id = {self.TABLE}.id AND vaz.zone IN ({', '.join(phs)}))"
                )

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, external_id, valet_id, date, availability_type, created_at, updated_at FROM {self.TABLE}{where_sql} ORDER BY date ASC, id ASC"
                ),
                params,
            )
            rows = result.fetchall()
            if not rows:
                return []

            ids = [r.id for r in rows]
            slots_map: dict[int, list[str]] = {cid: [] for cid in ids}
            zones_map: dict[int, list[str]] = {cid: [] for cid in ids}

            id_phs = [f":bid_{i}" for i in range(len(ids))]
            id_params: dict[str, object] = {f"bid_{i}": cid for i, cid in enumerate(ids)}

            slots_res = await session.execute(
                text(
                    f"SELECT availability_id, slot FROM sj_valet_availability_slots WHERE availability_id IN ({', '.join(id_phs)}) ORDER BY id ASC"
                ),
                id_params,
            )
            for sr in slots_res.fetchall():
                if sr.availability_id in slots_map:
                    slots_map[sr.availability_id].append(sr.slot)

            zones_res = await session.execute(
                text(
                    f"SELECT availability_id, zone FROM sj_valet_availability_zones WHERE availability_id IN ({', '.join(id_phs)}) ORDER BY id ASC"
                ),
                id_params,
            )
            for zr in zones_res.fetchall():
                if zr.availability_id in zones_map:
                    zones_map[zr.availability_id].append(zr.zone)

            return [
                _map_row(r, slots_map.get(r.id, []), zones_map.get(r.id, []))
                for r in rows
            ]

    async def findOne(
        self, filters: Optional[ValetAvailabilityFilter] = None
    ) -> Optional[ValetAvailability]:
        docs = await self.findAll(filters=filters)
        return docs[0] if docs else None

    async def findById(self, id: str) -> Optional[ValetAvailability]:
        return await self.findOne(ValetAvailabilityFilter(id=id))

    async def count(
        self, filters: Optional[ValetAvailabilityFilter] = None
    ) -> int:
        factory = self._factory()
        if not factory:
            return 0

        where_clauses: list[str] = []
        params: dict[str, object] = {}

        if filters is not None:
            if filters.id is not None:
                where_clauses.append("id = :id")
                params["id"] = int(filters.id) if str(filters.id).isdigit() else str(filters.id)
            if filters.valet_id is not None:
                where_clauses.append("valet_id = :valet_id")
                params["valet_id"] = str(filters.valet_id)
            if filters.date is not None:
                where_clauses.append("date = :date")
                params["date"] = str(filters.date)
            if filters.availability_type is not None:
                where_clauses.append("availability_type = :atype")
                params["atype"] = str(filters.availability_type)
            if filters.start_date is not None:
                where_clauses.append("date >= :start_date")
                params["start_date"] = str(filters.start_date)
            if filters.end_date is not None:
                where_clauses.append("date <= :end_date")
                params["end_date"] = str(filters.end_date)
            if filters.seller_zones is not None and len(filters.seller_zones) > 0:
                phs = [f":sz_{i}" for i in range(len(filters.seller_zones))]
                for i, sz in enumerate(filters.seller_zones):
                    params[f"sz_{i}"] = str(sz)
                where_clauses.append(
                    f"EXISTS (SELECT 1 FROM sj_valet_availability_zones vaz WHERE vaz.availability_id = {self.TABLE}.id AND vaz.zone IN ({', '.join(phs)}))"
                )

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM {self.TABLE}{where_sql}"),
                params,
            )
            return int(result.scalar() or 0)

    async def create(self, data: ValetAvailabilityInternalCreate) -> ValetAvailability:
        factory = self._factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        external_id = secrets.token_hex(16)

        async with factory() as session:
            result = await session.execute(
                text(f"""
                    INSERT INTO {self.TABLE} (external_id, valet_id, date, availability_type, created_at, updated_at) 
                    VALUES (:external_id, :valet_id, :date, :availability_type, :created_at, :updated_at)
                """),
                {
                    "external_id": external_id,
                    "valet_id": str(data.valet_id or ""),
                    "date": str(data.date) if data.date else None,
                    "availability_type": str(data.availability_type or ""),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            new_id = result.lastrowid

            if data.slots:
                for slot in data.slots:
                    await session.execute(
                        text("INSERT INTO sj_valet_availability_slots (availability_id, slot) VALUES (:vid, :s)"),
                        {"vid": new_id, "s": str(slot)},
                    )

            if data.zones:
                for zone in data.zones:
                    await session.execute(
                        text("INSERT INTO sj_valet_availability_zones (availability_id, zone) VALUES (:vid, :z)"),
                        {"vid": new_id, "z": str(zone)},
                    )

            await session.commit()

        created = await self.findById(str(new_id))
        if not created:
            raise RuntimeError(f"Failed to load newly created availability record {new_id}")
        return created

    async def update(
        self, id: str, update_data: ValetAvailabilityInternalUpdate
    ) -> Optional[ValetAvailability]:
        factory = self._factory()
        if not factory:
            return None
        pk = int(id) if str(id).isdigit() else None
        if pk is None:
            return None

        now = now_utc()
        set_clauses: list[str] = ["updated_at = :up"]
        params: dict[str, object] = {"id": pk, "up": now}

        if update_data.valet_id is not None:
            set_clauses.append("valet_id = :valet_id")
            params["valet_id"] = str(update_data.valet_id)
        if update_data.date is not None:
            set_clauses.append("date = :date")
            params["date"] = str(update_data.date)
        if update_data.availability_type is not None:
            set_clauses.append("availability_type = :atype")
            params["atype"] = str(update_data.availability_type)

        async with factory() as session:
            await session.execute(
                text(f"UPDATE {self.TABLE} SET {', '.join(set_clauses)} WHERE id = :id"),
                params,
            )

            if update_data.slots is not None:
                await session.execute(
                    text("DELETE FROM sj_valet_availability_slots WHERE availability_id = :vid"),
                    {"vid": pk},
                )
                for slot in update_data.slots:
                    await session.execute(
                        text("INSERT INTO sj_valet_availability_slots (availability_id, slot) VALUES (:vid, :s)"),
                        {"vid": pk, "s": str(slot)},
                    )

            if update_data.zones is not None:
                await session.execute(
                    text("DELETE FROM sj_valet_availability_zones WHERE availability_id = :vid"),
                    {"vid": pk},
                )
                for zone in update_data.zones:
                    await session.execute(
                        text("INSERT INTO sj_valet_availability_zones (availability_id, zone) VALUES (:vid, :z)"),
                        {"vid": pk, "z": str(zone)},
                    )

            await session.commit()

        return await self.findById(str(pk))

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pk = int(id) if str(id).isdigit() else None
        if pk is None:
            return False
        async with factory() as session:
            res = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pk})
            await session.commit()
            return res.rowcount > 0

    # ─── Native SQL Pushdown Methods ──────────────────────────────────────────

    async def get_my_upcoming_availability(
        self, valet_id: str, start_date: str, end_date: str
    ) -> list[ValetAvailability]:
        """Fetch valet's upcoming availability in a date range via pushdown SQL, ordered by date ASC."""
        return await self.findAll(
            ValetAvailabilityFilter(
                valet_id=valet_id,
                start_date=start_date,
                end_date=end_date,
            )
        )

    async def upsert_availability(
        self, data: ValetAvailabilityInternalCreate
    ) -> ValetAvailability:
        """Upsert availability for a valet on a date."""
        existing = await self.findOne(
            ValetAvailabilityFilter(valet_id=data.valet_id, date=data.date)
        )
        if existing and existing.id:
            updated = await self.update(
                existing.id,
                ValetAvailabilityInternalUpdate(
                    valet_id=data.valet_id,
                    date=data.date,
                    availability_type=data.availability_type,
                    slots=data.slots,
                    zones=data.zones,
                ),
            )
            if updated:
                return updated
        return await self.create(data)
