from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import CoachMarkInternal, CoachMarkInternalCreate, CoachMarkInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLCoachMarksDAO:
    def __init__(self):
        self.table_name = "sj_coach_marks"
    
    @property
    def TABLE(self):
        return self.table_name

    async def findById(self, id: int) -> Optional[CoachMarkInternal]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": id})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findByAnchorId(self, anchor_id: str) -> Optional[CoachMarkInternal]:
        if not anchor_id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE anchor_id = :anchor_id LIMIT 1")
            result = await session.execute(q, {"anchor_id": anchor_id})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findOne(
        self,
        id: Optional[int] = None,
        anchor_id: Optional[str] = None,
    ) -> Optional[CoachMarkInternal]:
        if anchor_id:
            return await self.findByAnchorId(anchor_id)
        if id:
            return await self.findById(id)
        all_marks = await self.findAll()
        return all_marks[0] if all_marks else None
            
    async def findAll(
        self,
        screen_name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[CoachMarkInternal]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            clauses = []
            params = {}

            if is_active is not None:
                clauses.append("is_active = :act")
                params["act"] = 1 if is_active else 0
            if screen_name is not None:
                clauses.append("screen_name = :screen_name")
                params["screen_name"] = str(screen_name)

            sql = f"SELECT * FROM {self.TABLE}"
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            sql += " ORDER BY sequence_order ASC"
                    
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

    async def create(self, data: CoachMarkInternalCreate) -> CoachMarkInternal:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database session factory unavailable")
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        val_placeholders = [":c", ":u"]
        params = {"c": now, "u": now}

        if data.anchor_id is not None:
            cols.append("anchor_id")
            val_placeholders.append(":anchor_id")
            params["anchor_id"] = data.anchor_id

        if data.title is not None:
            cols.append("title")
            val_placeholders.append(":title")
            params["title"] = data.title

        if data.description is not None:
            cols.append("description")
            val_placeholders.append(":description")
            params["description"] = data.description

        if data.screen_name is not None:
            cols.append("screen_name")
            val_placeholders.append(":screen_name")
            params["screen_name"] = data.screen_name

        if data.sequence_order is not None:
            cols.append("sequence_order")
            val_placeholders.append(":sequence_order")
            params["sequence_order"] = data.sequence_order

        if data.is_active is not None:
            cols.append("is_active")
            val_placeholders.append(":is_active")
            params["is_active"] = 1 if data.is_active else 0

        col_sql = ", ".join(cols)
        val_sql = ", ".join(val_placeholders)
        
        async with async_session() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: CoachMarkInternalUpdate) -> Optional[CoachMarkInternal]:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return None
            
        fields = update_data.model_fields_set
        if not fields:
            return await self.findById(id)

        updates = ["updated_at = :u"]
        params = {"u": now_utc(), "pk": id}

        if "anchor_id" in fields:
            updates.append("anchor_id = :anchor_id")
            params["anchor_id"] = update_data.anchor_id

        if "title" in fields:
            updates.append("title = :title")
            params["title"] = update_data.title

        if "description" in fields:
            updates.append("description = :description")
            params["description"] = update_data.description

        if "screen_name" in fields:
            updates.append("screen_name = :screen_name")
            params["screen_name"] = update_data.screen_name

        if "sequence_order" in fields:
            updates.append("sequence_order = :sequence_order")
            params["sequence_order"] = update_data.sequence_order

        if "is_active" in fields:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if update_data.is_active else 0

        upd_sql = ", ".join(updates)

        async with async_session() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :pk"), params)
            await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return False
        async with async_session() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :pk"),
                {"pk": id},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r) -> CoachMarkInternal:
        return CoachMarkInternal(
            id=str(r.id),
            anchor_id=r.anchor_id,
            title=r.title,
            description=r.description,
            screen_name=r.screen_name,
            sequence_order=int(r.sequence_order) if r.sequence_order is not None else None,
            is_active=bool(r.is_active) if r.is_active is not None else True,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
