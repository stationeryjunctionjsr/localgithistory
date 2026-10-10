from typing import Optional, Dict, List, Any
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
        
    async def findById(self, id: str) -> Optional[CoachMarkInternal]:
        pk = int(id) if str(id).isdigit() else None
        if pk is None:
            return None
        async with self._factory()() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            result = await session.execute(q, {"id": pk})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findByAnchorId(self, anchor_id: str) -> Optional[CoachMarkInternal]:
        async with self._factory()() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE anchor_id = :anchor_id LIMIT 1")
            result = await session.execute(q, {"anchor_id": anchor_id})
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)

    async def findOne(self, query: Optional[dict] = None, **kwargs) -> Optional[CoachMarkInternal]:
        params_dict = {}
        if query:
            params_dict.update(query)
        params_dict.update(kwargs)
        if not params_dict:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params: Dict[str, Any] = {}
            for k, v in params_dict.items():
                if k in ("_id", "id"):
                    conditions.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else v
                elif k in ("externalId", "external_id"):
                    conditions.append("external_id = :external_id")
                    params["external_id"] = str(v)
                elif k in ("anchorId", "anchor_id"):
                    conditions.append("anchor_id = :anchor_id")
                    params["anchor_id"] = str(v)
                elif k in ("screenName", "screen_name"):
                    conditions.append("screen_name = :screen_name")
                    params["screen_name"] = str(v)
                elif k in ("isActive", "is_active"):
                    conditions.append("is_active = :is_active")
                    params["is_active"] = 1 if v else 0
                elif k in ("sequenceOrder", "sequence_order"):
                    conditions.append("sequence_order = :sequence_order")
                    params["sequence_order"] = int(v)
                else:
                    conditions.append(f"{k} = :{k}")
                    params[k] = v
                
            where_clause = " AND ".join(conditions)
            q = text(f"SELECT * FROM {self.TABLE} WHERE {where_clause} LIMIT 1")
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            return self._map_to_schema(row)
            
    async def findAll(
        self,
        query: Optional[dict] = None,
        screen_name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[CoachMarkInternal]:
        if is_active is None and query:
            val = query.get("isActive") if "isActive" in query else query.get("is_active")
            if val is not None:
                is_active = bool(val)
        if screen_name is None and query:
            screen_name = query.get("screenName") or query.get("screen_name")

        async with self._factory()() as session:
            conditions = []
            params: Dict[str, Any] = {}

            if is_active is not None:
                conditions.append("is_active = :is_active")
                params["is_active"] = 1 if is_active else 0
            if screen_name is not None:
                conditions.append("screen_name = :screen_name")
                params["screen_name"] = screen_name

            if query:
                for k, v in query.items():
                    if k in ("isActive", "is_active", "screenName", "screen_name"):
                        continue
                    if k in ("_id", "id"):
                        conditions.append("id = :id")
                        params["id"] = int(v) if str(v).isdigit() else v
                    elif k in ("externalId", "external_id"):
                        conditions.append("external_id = :external_id")
                        params["external_id"] = str(v)
                    elif k in ("anchorId", "anchor_id"):
                        conditions.append("anchor_id = :anchor_id")
                        params["anchor_id"] = str(v)
                    elif k in ("sequenceOrder", "sequence_order"):
                        conditions.append("sequence_order = :sequence_order")
                        params["sequence_order"] = int(v)
                    else:
                        conditions.append(f"{k} = :{k}")
                        params[k] = v
                        
            sql = f"SELECT * FROM {self.TABLE}"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY sequence_order ASC"
                    
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            return [self._map_to_schema(r) for r in rows]

    async def create(self, data: CoachMarkInternalCreate) -> CoachMarkInternal:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        val_placeholders = [":eid", ":c", ":u"]
        params: Dict[str, Any] = {"eid": external_id, "c": now, "u": now}

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
            
        return await self.findById(str(new_id))

    async def update(self, id: str, update_data: CoachMarkInternalUpdate) -> CoachMarkInternal:
        factory = self._factory()
        updates = ["updated_at = :u"]
        pk = int(id) if str(id).isdigit() else None
        params: Dict[str, Any] = {"id": pk, "u": now_utc()}

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
            if pk is not None:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await session.commit()
                
        return await self.findById(str(id))

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pk = int(id) if str(id).isdigit() else None
        if pk is None:
            return False
        async with factory() as session:
            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r) -> CoachMarkInternal:
        return CoachMarkInternal(
            id=str(r.id),
            external_id=getattr(r, "external_id", None),
            anchor_id=getattr(r, "anchor_id", None),
            title=getattr(r, "title", None),
            description=getattr(r, "description", None),
            screen_name=getattr(r, "screen_name", None),
            sequence_order=int(r.sequence_order) if getattr(r, "sequence_order", None) is not None else None,
            is_active=bool(r.is_active) if getattr(r, "is_active", None) is not None else True,
            created_at=getattr(r, "created_at", None),
            updated_at=getattr(r, "updated_at", None),
        )
