"""
MySQL DAO for seller availability windows.
Fully normalized relational storage: no doc JSON.
Table: sj_seller_availability
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text

from app.config.database import get_async_session_factory
from app.models.seller_availability import SellerAvailability, SellerAvailabilityEnriched
from app.models.daos_flat import (
    SellerAvailabilityFilter,
    SellerAvailabilityInternalCreate,
    SellerAvailabilityInternalUpdate,
)

logger = logging.getLogger(__name__)


def _to_dt(v: Optional[datetime | str]) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception as e:
        logger.warning("mysql_seller_availability_dao._to_dt: could not parse datetime %r: %s", v, e, exc_info=e)
        return None


class MySQLSellerAvailabilityDAO:
    @property
    def table_name(self) -> str:
        return "sj_seller_availability"

    def _get_session_factory(self):
        return get_async_session_factory()

    def __map_to_schema(self, row) -> SellerAvailability:
        return SellerAvailability.model_validate(row)

    async def findAll(
        self,
        filters: Optional[SellerAvailabilityFilter] = None,
    ) -> list[SellerAvailability]:
        factory = self._get_session_factory()
        if not factory:
            return []

        where_clauses: list[str] = []
        params = {}

        if filters is not None:
            if filters.id is not None:
                where_clauses.append("id = :q_id")
                params["q_id"] = int(filters.id) if str(filters.id).isdigit() else str(filters.id)

            if filters.seller_id is not None:
                where_clauses.append("seller_id = :seller_id")
                params["seller_id"] = str(filters.seller_id)

            if filters.statuses is not None and len(filters.statuses) > 0:
                phs = [f":st_{i}" for i in range(len(filters.statuses))]
                for i, st in enumerate(filters.statuses):
                    params[f"st_{i}"] = str(st)
                where_clauses.append(f"status IN ({', '.join(phs)})")
            elif filters.status is not None:
                where_clauses.append("status = :status")
                params["status"] = str(filters.status)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        async with factory() as session:
            result = await session.execute(
                text(
                    f"SELECT id, seller_id, status, start_at, end_at, reason, created_by, cancelled_at, created_at, updated_at FROM {self.table_name}{where_sql} ORDER BY start_at DESC"
                ),
                params,
            )
            return [self.__map_to_schema(r) for r in result.fetchall()]

    async def findOne(
        self,
        filters: Optional[SellerAvailabilityFilter] = None,
    ) -> Optional[SellerAvailability]:
        records = await self.findAll(filters=filters)
        return records[0] if records else None

    async def findById(self, id: str) -> Optional[SellerAvailability]:
        return await self.findOne(SellerAvailabilityFilter(id=id))

    async def count(
        self,
        filters: Optional[SellerAvailabilityFilter] = None,
    ) -> int:
        factory = self._get_session_factory()
        if not factory:
            return 0

        where_clauses: list[str] = []
        params = {}

        if filters is not None:
            if filters.id is not None:
                where_clauses.append("id = :q_id")
                params["q_id"] = int(filters.id) if str(filters.id).isdigit() else str(filters.id)

            if filters.seller_id is not None:
                where_clauses.append("seller_id = :seller_id")
                params["seller_id"] = str(filters.seller_id)

            if filters.statuses is not None and len(filters.statuses) > 0:
                phs = [f":st_{i}" for i in range(len(filters.statuses))]
                for i, st in enumerate(filters.statuses):
                    params[f"st_{i}"] = str(st)
                where_clauses.append(f"status IN ({', '.join(phs)})")
            elif filters.status is not None:
                where_clauses.append("status = :status")
                params["status"] = str(filters.status)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        async with factory() as session:
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM {self.table_name}{where_sql}"),
                params,
            )
            return int(result.scalar() or 0)

    async def create(self, data: SellerAvailabilityInternalCreate) -> SellerAvailability:
        factory = self._get_session_factory()
        if not factory:
            raise RuntimeError("MySQL not configured")
        now = datetime.now(timezone.utc)
        params = {
            "seller_id": str(data.seller_id or ""),
            "status": (data.status if data.status is not None else "scheduled"),
            "start_at": _to_dt(data.start_at),
            "end_at": _to_dt(data.end_at),
            "reason": data.reason,
            "created_by": data.created_by,
            "cancelled_at": _to_dt(data.cancelled_at),
            "created_at": now,
            "updated_at": now,
        }
        sql = text(f"""
            INSERT INTO {self.table_name}
                (seller_id, status, start_at, end_at, reason, created_by, cancelled_at, created_at, updated_at)
            VALUES
                (:seller_id, :status, :start_at, :end_at, :reason, :created_by, :cancelled_at, :created_at, :updated_at)
        """)
        async with factory() as session:
            result = await session.execute(sql, params)
            await session.commit()
            new_id = result.lastrowid
        return await self.findById(str(new_id))

    async def update(
        self, id: str, update_data: SellerAvailabilityInternalUpdate
    ) -> Optional[SellerAvailability]:
        factory = self._get_session_factory()
        if not factory:
            return None
        now = datetime.now(timezone.utc)
        row_id = int(id) if str(id).isdigit() else id
        set_clauses: list[str] = ["updated_at = :updated_at"]
        params = {"updated_at": now, "row_id": row_id}

        if update_data.status is not None:
            set_clauses.append("status = :status")
            params["status"] = update_data.status
        if update_data.seller_id is not None:
            set_clauses.append("seller_id = :seller_id")
            params["seller_id"] = update_data.seller_id
        if update_data.start_at is not None:
            set_clauses.append("start_at = :start_at")
            params["start_at"] = _to_dt(update_data.start_at)
        if update_data.end_at is not None:
            set_clauses.append("end_at = :end_at")
            params["end_at"] = _to_dt(update_data.end_at)
        if update_data.reason is not None:
            set_clauses.append("reason = :reason")
            params["reason"] = update_data.reason
        if update_data.created_by is not None:
            set_clauses.append("created_by = :created_by")
            params["created_by"] = update_data.created_by
        if update_data.cancelled_at is not None:
            set_clauses.append("cancelled_at = :cancelled_at")
            params["cancelled_at"] = _to_dt(update_data.cancelled_at)

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

    # ─── Native SQL Pushdown Business Methods ─────────────────────────────────

    async def is_seller_currently_unavailable(
        self, seller_id: str, as_of: Optional[datetime] = None
    ) -> bool:
        """Check whether a seller has an active unavailability window right now via indexed pushdown SQL."""
        factory = self._get_session_factory()
        if not factory:
            return False
        check_time = as_of or datetime.now(timezone.utc)
        sql = text(f"""
            SELECT 1 FROM {self.table_name}
            WHERE seller_id = :seller_id
              AND status IN ('scheduled', 'active')
              AND start_at <= :check_time
              AND end_at >= :check_time
            LIMIT 1
        """)
        async with factory() as session:
            result = await session.execute(sql, {"seller_id": seller_id, "check_time": check_time})
            return result.scalar() is not None

    async def get_currently_unavailable_seller_ids(
        self, as_of: Optional[datetime] = None
    ) -> set[str]:
        """Fetch all unique seller IDs currently within an unavailability window via pushdown SQL."""
        factory = self._get_session_factory()
        if not factory:
            return set()
        check_time = as_of or datetime.now(timezone.utc)
        sql = text(f"""
            SELECT DISTINCT seller_id FROM {self.table_name}
            WHERE status IN ('scheduled', 'active')
              AND start_at <= :check_time
              AND end_at >= :check_time
        """)
        async with factory() as session:
            result = await session.execute(sql, {"check_time": check_time})
            return {str(row.seller_id) for row in result.fetchall() if row.seller_id}

    async def get_latest_unavailable_until(
        self, seller_ids: set[str], as_of: Optional[datetime] = None
    ) -> Optional[str]:
        """Find latest end_at timestamp across active windows for given sellers via pushdown SQL MAX()."""
        if not seller_ids:
            return None
        factory = self._get_session_factory()
        if not factory:
            return None
        check_time = as_of or datetime.now(timezone.utc)
        sids = list(seller_ids)
        phs = [f":sid_{i}" for i in range(len(sids))]
        params = {"check_time": check_time}
        for i, sid in enumerate(sids):
            params[f"sid_{i}"] = str(sid)
        sql = text(f"""
            SELECT MAX(end_at) FROM {self.table_name}
            WHERE seller_id IN ({', '.join(phs)})
              AND status IN ('scheduled', 'active')
              AND start_at <= :check_time
              AND end_at >= :check_time
        """)
        async with factory() as session:
            result = await session.execute(sql, params)
            val = result.scalar()
            if val is None:
                return None
            dt = _to_dt(val)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else None

    async def get_zone_unavailable_sellers_map(
        self, seller_ids: set[str], as_of: Optional[datetime] = None
    ):
        """Fetch map of seller_id -> latest end_at ISO string via pushdown SQL GROUP BY."""
        if not seller_ids:
            return {}
        factory = self._get_session_factory()
        if not factory:
            return {}
        check_time = as_of or datetime.now(timezone.utc)
        sids = list(seller_ids)
        phs = [f":sid_{i}" for i in range(len(sids))]
        params = {"check_time": check_time}
        for i, sid in enumerate(sids):
            params[f"sid_{i}"] = str(sid)
        sql = text(f"""
            SELECT seller_id, MAX(end_at) AS max_end_at FROM {self.table_name}
            WHERE seller_id IN ({', '.join(phs)})
              AND status IN ('scheduled', 'active')
              AND start_at <= :check_time
              AND end_at >= :check_time
            GROUP BY seller_id
        """)
        async with factory() as session:
            result = await session.execute(sql, params)
            output = {}
            for row in result.fetchall():
                sid, val = str(row.seller_id), row.max_end_at
                dt = _to_dt(val)
                if dt:
                    output[sid] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            return output

    async def advance_availability_statuses(
        self, as_of: Optional[datetime] = None
    ) -> tuple[int, int]:
        """Advance scheduled -> active and active -> ended in atomic batch updates without row-by-row loops."""
        factory = self._get_session_factory()
        if not factory:
            return 0, 0
        now = as_of or datetime.now(timezone.utc)
        async with factory() as session:
            res_active = await session.execute(
                text(f"""
                    UPDATE {self.table_name}
                    SET status = 'active', updated_at = :now
                    WHERE status = 'scheduled' AND start_at <= :now
                """),
                {"now": now},
            )
            res_ended = await session.execute(
                text(f"""
                    UPDATE {self.table_name}
                    SET status = 'ended', updated_at = :now
                    WHERE status = 'active' AND end_at <= :now
                """),
                {"now": now},
            )
            await session.commit()
            return int(res_active.rowcount), int(res_ended.rowcount)

    async def find_all_with_seller_details(
        self, filters: Optional[SellerAvailabilityFilter] = None
    ) -> list[SellerAvailabilityEnriched]:
        """Fetch all availability windows joined with user details, sorted by start_at DESC via native SQL."""
        factory = self._get_session_factory()
        if not factory:
            return []

        where_clauses: list[str] = []
        params = {}

        if filters is not None:
            if filters.id is not None:
                where_clauses.append("sa.id = :q_id")
                params["q_id"] = int(filters.id) if str(filters.id).isdigit() else str(filters.id)

            if filters.seller_id is not None:
                where_clauses.append("sa.seller_id = :seller_id")
                params["seller_id"] = str(filters.seller_id)

            if filters.statuses is not None and len(filters.statuses) > 0:
                phs = [f":st_{i}" for i in range(len(filters.statuses))]
                for i, st in enumerate(filters.statuses):
                    params[f"st_{i}"] = str(st)
                where_clauses.append(f"sa.status IN ({', '.join(phs)})")
            elif filters.status is not None:
                where_clauses.append("sa.status = :status")
                params["status"] = str(filters.status)

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        sql = text(f"""
            SELECT 
                sa.id, sa.seller_id, sa.status, sa.start_at, sa.end_at, 
                sa.reason, sa.created_by, sa.cancelled_at, sa.created_at, sa.updated_at,
                u.name AS seller_name, u.email AS seller_email
            FROM {self.table_name} sa
            LEFT JOIN sj_users u ON sa.seller_id = CAST(u.id AS CHAR)
            {where_sql}
            ORDER BY sa.start_at DESC
        """)
        async with factory() as session:
            result = await session.execute(sql, params)
            return [SellerAvailabilityEnriched.model_validate(r) for r in result.fetchall()]
