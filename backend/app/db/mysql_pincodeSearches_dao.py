"""
Strict SQLAlchemy DAO for sj_pincode_searches with native integer IDs and Pydantic models.
"""
from typing import Dict, List, Optional
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.db.db_utils import now_utc
from app.models.pincode_searches import PincodeSearches, PincodeSearchStatsResponse, PincodeStatItem
from app.models.daos_flat import (
    PincodeSearchesInternalCreate,
    PincodeSearchesInternalUpdate,
)


class MySQLPincodeSearchesDAO:
    TABLE = "sj_pincode_searches"

    def _map_to_schema(self, row) -> PincodeSearches:
        return PincodeSearches(
            id=row.id,
            pincode=row.pincode,
            query=row.query if "query" in row._mapping else None,
            is_serviceable=bool(row.is_serviceable) if ("is_serviceable" in row._mapping and row.is_serviceable is not None) else False,
            timestamp=row.timestamp.isoformat() if ("timestamp" in row._mapping and row.timestamp) else None,
            city=row.city if "city" in row._mapping else None,
            state=row.state if "state" in row._mapping else None,
            district=row.district if "district" in row._mapping else None,
            created_at=row.created_at if "created_at" in row._mapping else None,
            updated_at=row.updated_at if "updated_at" in row._mapping else None,
        )

    async def findAll(self, query: Optional[Dict] = None) -> List[PincodeSearches]:
        query = query or {}
        where_clauses = []
        params = {}
        if "pincode" in query:
            where_clauses.append("pincode = :pincode")
            params["pincode"] = query["pincode"]
        if "query" in query:
            where_clauses.append("query = :query")
            params["query"] = query["query"]
        if "isServiceable" in query or "is_serviceable" in query:
            val = query.get("isServiceable") if "isServiceable" in query else query.get("is_serviceable")
            where_clauses.append("is_serviceable = :isServiceable")
            params["isServiceable"] = 1 if val else 0
        if "timestamp" in query:
            where_clauses.append("timestamp = :timestamp")
            params["timestamp"] = query["timestamp"]

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            rows = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id ASC"),
                    params,
                )
            ).fetchall()
        return [self._map_to_schema(r) for r in rows]

    async def find_paginated(
        self,
        is_serviceable: Optional[bool] = None,
        search: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[PincodeSearches], int]:
        where_clauses = []
        params = {}
        if is_serviceable is not None:
            where_clauses.append("is_serviceable = :is_serv")
            params["is_serv"] = 1 if is_serviceable else 0
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            where_clauses.append("(LOWER(pincode) LIKE :term OR LOWER(city) LIKE :term OR LOWER(state) LIKE :term OR LOWER(district) LIKE :term)")
            params["term"] = term
        if start_date:
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end_date

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async_session = get_async_session_factory()
        if not async_session:
            return [], 0
        async with async_session() as session:
            count_q = text(f"SELECT COUNT(*) FROM {self.TABLE} WHERE {where_sql}")
            total = (await session.execute(count_q, params)).scalar() or 0

            data_q = text(f"SELECT * FROM {self.TABLE} WHERE {where_sql} ORDER BY id DESC LIMIT :limit OFFSET :skip")
            params_data = {**params, "limit": limit, "skip": skip}
            rows = (await session.execute(data_q, params_data)).fetchall()
            return [self._map_to_schema(r) for r in rows], total

    async def get_stats(self) -> PincodeSearchStatsResponse:
        """SQL pushdown to compute summary statistics on pincode searches without full table memory dump."""
        async_session = get_async_session_factory()
        if not async_session:
            return PincodeSearchStatsResponse()
        async with async_session() as session:
            summary_q = text(
                f"""
                SELECT 
                    COUNT(*) AS total_searches,
                    COUNT(DISTINCT pincode) AS unique_pincodes,
                    COUNT(CASE WHEN is_serviceable = 1 THEN 1 END) AS serviceable_searches,
                    COUNT(CASE WHEN is_serviceable = 0 THEN 1 END) AS unserviceable_searches
                FROM {self.TABLE}
                WHERE pincode IS NOT NULL AND pincode != ''
                """
            )
            agg = (await session.execute(summary_q)).fetchone()
            total_searches = agg.total_searches or 0 if agg else 0
            unique_pincodes = agg.unique_pincodes or 0 if agg else 0
            serviceable_searches = agg.serviceable_searches or 0 if agg else 0
            unserviceable_searches = agg.unserviceable_searches or 0 if agg else 0

            unserv_q = text(
                f"""
                SELECT pincode, MAX(city) AS city, MAX(state) AS state, COUNT(*) AS count, MAX(created_at) AS last_searched_at
                FROM {self.TABLE}
                WHERE is_serviceable = 0 AND pincode IS NOT NULL AND pincode != ''
                GROUP BY pincode
                ORDER BY count DESC
                LIMIT 10
                """
            )
            unserv_rows = (await session.execute(unserv_q)).fetchall()
            top_unserviceable = [
                PincodeStatItem(
                    pincode=r.pincode,
                    city=r.city,
                    state=r.state,
                    is_serviceable=False,
                    count=r.count or 0,
                    last_searched_at=r.last_searched_at.isoformat() if r.last_searched_at else None,
                )
                for r in unserv_rows
            ]

            searched_q = text(
                f"""
                SELECT pincode, MAX(city) AS city, MAX(state) AS state, MAX(is_serviceable) AS is_serviceable, COUNT(*) AS count, MAX(created_at) AS last_searched_at
                FROM {self.TABLE}
                WHERE pincode IS NOT NULL AND pincode != ''
                GROUP BY pincode
                ORDER BY count DESC
                LIMIT 10
                """
            )
            searched_rows = (await session.execute(searched_q)).fetchall()
            top_searched = [
                PincodeStatItem(
                    pincode=r.pincode,
                    city=r.city,
                    state=r.state,
                    is_serviceable=bool(r.is_serviceable),
                    count=r.count or 0,
                    last_searched_at=r.last_searched_at.isoformat() if r.last_searched_at else None,
                )
                for r in searched_rows
            ]

            return PincodeSearchStatsResponse(
                total_searches=total_searches,
                unique_pincodes=unique_pincodes,
                unique_pincodes_count=unique_pincodes,
                serviceable_searches=serviceable_searches,
                unserviceable_searches=unserviceable_searches,
                top_unserviceable_pincodes=top_unserviceable,
                top_searched_pincodes=top_searched,
                top_pincodes=top_searched,
            )

    async def findOne(self, query: Dict) -> Optional[PincodeSearches]:
        if "id" in query and query["id"]:
            return await self.findById(query["id"])
        records = await self.findAll(query)
        return records[0] if records else None

    async def findById(self, id: int) -> Optional[PincodeSearches]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            row = (
                await session.execute(
                    text(f"SELECT * FROM {self.TABLE} WHERE id = :id"),
                    {"id": id},
                )
            ).fetchone()
        return self._map_to_schema(row) if row else None

    async def create(self, data: PincodeSearchesInternalCreate) -> PincodeSearches:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("MySQL not configured")
        now = now_utc()
        cols = ["created_at", "updated_at"]
        vals = [":c", ":u"]
        params = {"c": now, "u": now}
        if data.pincode is not None:
            cols.append("pincode")
            vals.append(":pincode")
            params["pincode"] = data.pincode
        if data.query is not None:
            cols.append("query")
            vals.append(":query")
            params["query"] = data.query
        if data.is_serviceable is not None:
            cols.append("is_serviceable")
            vals.append(":is_serviceable")
            params["is_serviceable"] = 1 if data.is_serviceable else 0
        if data.timestamp is not None:
            cols.append("timestamp")
            vals.append(":timestamp")
            params["timestamp"] = data.timestamp
        if data.city is not None:
            cols.append("city")
            vals.append(":city")
            params["city"] = data.city
        if data.state is not None:
            cols.append("state")
            vals.append(":state")
            params["state"] = data.state
        if data.district is not None:
            cols.append("district")
            vals.append(":district")
            params["district"] = data.district

        col_sql = ", ".join(cols)
        val_sql = ", ".join(vals)
        async with async_session() as session:
            res = await session.execute(
                text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"),
                params,
            )
            new_id = res.lastrowid
            await session.commit()
        return await self.findById(new_id)

    async def update(self, id: int, data: PincodeSearchesInternalUpdate) -> Optional[PincodeSearches]:
        if not id:
            return None

        now = now_utc()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now}
        if "pincode" in data.model_fields_set and data.pincode is not None:
            updates.append("pincode = :pincode")
            params["pincode"] = data.pincode
        if "query" in data.model_fields_set and data.query is not None:
            updates.append("query = :query")
            params["query"] = data.query
        if "is_serviceable" in data.model_fields_set and data.is_serviceable is not None:
            updates.append("is_serviceable = :is_serviceable")
            params["is_serviceable"] = 1 if data.is_serviceable else 0
        if "timestamp" in data.model_fields_set and data.timestamp is not None:
            updates.append("timestamp = :timestamp")
            params["timestamp"] = data.timestamp
        if "city" in data.model_fields_set and data.city is not None:
            updates.append("city = :city")
            params["city"] = data.city
        if "state" in data.model_fields_set and data.state is not None:
            updates.append("state = :state")
            params["state"] = data.state
        if "district" in data.model_fields_set and data.district is not None:
            updates.append("district = :district")
            params["district"] = data.district

        set_sql = ", ".join(updates)
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            res = await session.execute(
                text(f"UPDATE {self.TABLE} SET {set_sql} WHERE id = :id"),
                params,
            )
            if res.rowcount == 0:
                chk = await session.execute(text(f"SELECT id FROM {self.TABLE} WHERE id = :id"), {"id": id})
                if not chk.fetchone():
                    return None
            await session.commit()
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        if not id:
            return False
        async_session = get_async_session_factory()
        if not async_session:
            return False
        async with async_session() as session:
            res = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": id},
            )
            await session.commit()
            return res.rowcount > 0
