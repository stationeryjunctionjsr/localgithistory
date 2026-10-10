from typing import Optional, List, Union
from datetime import datetime, timezone
import secrets
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

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional[CoachMarkInternal]:
        if not id:
            return None
        async with self._factory()() as session:
            if str(id).isdigit():
                q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
                params = {"id": int(id)}
            else:
                q = text(f"SELECT * FROM {self.TABLE} WHERE external_id = :id LIMIT 1")
                params = {"id": str(id)}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findByAnchorId(self, anchor_id: str) -> Optional[CoachMarkInternal]:
        if not anchor_id:
            return None
        async with self._factory()() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE anchor_id = :anchor_id LIMIT 1")
            result = await session.execute(q, {"anchor_id": anchor_id})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findOne(
        self,
        anchor_id: Optional[str] = None,
        id: Optional[Union[int, str]] = None,
        query: Optional[dict] = None,
    ) -> Optional[CoachMarkInternal]:
        if query:
            anchor_id = query.get("anchor_id") or query.get("anchorId") or anchor_id
            id = query.get("id") or query.get("_id") or id
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
        query: Optional[dict] = None,
    ) -> List[CoachMarkInternal]:
        if query:
            if is_active is None:
                val = query.get("isActive") if "isActive" in query else query.get("is_active")
                if val is not None:
                    is_active = bool(val)
            if screen_name is None:
                screen_name = query.get("screenName") or query.get("screen_name")

        async with self._factory()() as session:
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
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        val_placeholders = [":eid", ":c", ":u"]
        params = {"eid": external_id, "c": now, "u": now}

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
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await session.commit()
            
        return await self.findById(int(new_id))

    async def update(self, id: Union[int, str], update_data: CoachMarkInternalUpdate) -> Optional[CoachMarkInternal]:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"u": now_utc()}

        if update_data.anchor_id is not None:
            updates.append("anchor_id = :anchor_id")
            params["anchor_id"] = update_data.anchor_id

        if update_data.title is not None:
            updates.append("title = :title")
            params["title"] = update_data.title

        if update_data.description is not None:
            updates.append("description = :description")
            params["description"] = update_data.description

        if update_data.screen_name is not None:
            updates.append("screen_name = :screen_name")
            params["screen_name"] = update_data.screen_name

        if update_data.sequence_order is not None:
            updates.append("sequence_order = :sequence_order")
            params["sequence_order"] = update_data.sequence_order

        if update_data.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = 1 if update_data.is_active else 0

        upd_sql = ", ".join(updates)
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
                upd_where = "id = :pk"
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return None
                upd_where = "id = :pk"
            params["pk"] = pk

            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE {upd_where}"), params)
            await session.commit()
                
        return await self.findById(pk)

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
                del_where = "id = :pk"
                params = {"pk": pk}
            else:
                del_where = "external_id = :eid"
                params = {"eid": str(id)}

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE {del_where}"),
                params,
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r) -> CoachMarkInternal:
        return CoachMarkInternal(
            id=str(r.id),
            external_id=r.external_id,
            anchor_id=r.anchor_id,
            title=r.title,
            description=r.description,
            screen_name=r.screen_name,
            sequence_order=int(r.sequence_order) if r.sequence_order is not None else None,
            is_active=bool(r.is_active) if r.is_active is not None else True,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
