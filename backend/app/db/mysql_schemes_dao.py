from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import SchemeInternal
from app.models.daos_flat import SchemeInternalCreate, SchemeInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLSchemesDAO:
    def __init__(self):
        self.table_name = "sj_schemes"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        suffix = (settings.table_suffix if settings.table_suffix is not None else "")
        return f"{self.table_name}{suffix}"

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: str) -> Optional[Any]:
        return await self.findOne({"_id": id})

    async def findOne(self, query=None, **kwargs) -> Optional[Any]:
        if query:
            kwargs.update(query)
        if not kwargs:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params = {}
            
            query_map = {'name': 'name', 'description': 'description', 'discountType': 'discount_type', 'discountValue': 'discount_value', 'minOrderValue': 'min_order_value', 'validFrom': 'valid_from', 'validUntil': 'valid_until', 'isActive': 'is_active', 'code': 'code'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            for k, v in kwargs.items():
                db_col = query_map.get(k, k)
                conditions.append(f"{db_col} = :{k}")
                params[k] = v
                
            where_clause = " AND ".join(conditions)
            q = text(f"SELECT * FROM {self.TABLE} WHERE {where_clause} LIMIT 1")
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
                
            children_map = await self._fetch_children(session, [int(row.id)]) if True else {}
            return self._map_to_schema(row, children_map.get(int(row.id), {}))
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[Any]:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'name': 'name', 'description': 'description', 'discountType': 'discount_type', 'discountValue': 'discount_value', 'minOrderValue': 'min_order_value', 'validFrom': 'valid_from', 'validUntil': 'valid_until', 'isActive': 'is_active', 'code': 'code'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            if query:
                conditions = []
                for k, v in query.items():
                    db_col = query_map.get(k, k)
                    conditions.append(f"{db_col} = :{k}")
                    params[k] = v
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
                    
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            
            if not rows:
                return []
                
            children_map = await self._fetch_children(session, [int(r.id) for r in rows]) if True else {}
            
            return [self._map_to_schema(r, children_map.get(int(r.id), {})) for r in rows]

    async def create(self, data: Any) -> Any:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if hasattr(data, "name") and getattr(data, "name") is not None:
            cols.append("name")
            params["s_name"] = getattr(data, "name")

        if hasattr(data, "description") and getattr(data, "description") is not None:
            cols.append("description")
            params["s_description"] = getattr(data, "description")

        if hasattr(data, "discountType") and getattr(data, "discountType") is not None:
            cols.append("discount_type")
            params["s_discountType"] = getattr(data, "discountType")

        if hasattr(data, "discountValue") and getattr(data, "discountValue") is not None:
            cols.append("discount_value")
            params["s_discountValue"] = getattr(data, "discountValue")

        if hasattr(data, "minOrderValue") and getattr(data, "minOrderValue") is not None:
            cols.append("min_order_value")
            params["s_minOrderValue"] = getattr(data, "minOrderValue")

        if hasattr(data, "validFrom") and getattr(data, "validFrom") is not None:
            cols.append("valid_from")
            params["s_validFrom"] = getattr(data, "validFrom")

        if hasattr(data, "validUntil") and getattr(data, "validUntil") is not None:
            cols.append("valid_until")
            params["s_validUntil"] = getattr(data, "validUntil")

        if hasattr(data, "isActive") and getattr(data, "isActive") is not None:
            cols.append("is_active")
            params["s_isActive"] = getattr(data, "isActive")

        if hasattr(data, "code") and getattr(data, "code") is not None:
            cols.append("code")
            params["s_code"] = getattr(data, "code")

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['name', 'description', 'discountType', 'discountValue', 'minOrderValue', 'validFrom', 'validUntil', 'isActive', 'code'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
        async with factory() as session:
            await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = (
                await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": external_id}
                )
            ).scalar()
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: str, data: Any) -> Any:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if hasattr(data, "name") and getattr(data, "name") is not None:
            updates.append("name = :s_name")
            params["s_name"] = getattr(data, "name")

        if hasattr(data, "description") and getattr(data, "description") is not None:
            updates.append("description = :s_description")
            params["s_description"] = getattr(data, "description")

        if hasattr(data, "discountType") and getattr(data, "discountType") is not None:
            updates.append("discount_type = :s_discountType")
            params["s_discountType"] = getattr(data, "discountType")

        if hasattr(data, "discountValue") and getattr(data, "discountValue") is not None:
            updates.append("discount_value = :s_discountValue")
            params["s_discountValue"] = getattr(data, "discountValue")

        if hasattr(data, "minOrderValue") and getattr(data, "minOrderValue") is not None:
            updates.append("min_order_value = :s_minOrderValue")
            params["s_minOrderValue"] = getattr(data, "minOrderValue")

        if hasattr(data, "validFrom") and getattr(data, "validFrom") is not None:
            updates.append("valid_from = :s_validFrom")
            params["s_validFrom"] = getattr(data, "validFrom")

        if hasattr(data, "validUntil") and getattr(data, "validUntil") is not None:
            updates.append("valid_until = :s_validUntil")
            params["s_validUntil"] = getattr(data, "validUntil")

        if hasattr(data, "isActive") and getattr(data, "isActive") is not None:
            updates.append("is_active = :s_isActive")
            params["s_isActive"] = getattr(data, "isActive")

        if hasattr(data, "code") and getattr(data, "code") is not None:
            updates.append("code = :s_code")
            params["s_code"] = getattr(data, "code")

        if len(updates) > 1:
            upd_sql = ", ".join(updates)
            async with factory() as session:
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :id"), params)
                await self._replace_children(session, int(id), data)
                await session.commit()
        else:
            async with factory() as session:
                await self._replace_children(session, int(id), data)
                await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: str) -> bool:
        factory = self._factory()
        if not factory:
            return False
        pk = int(id) if str(id).isdigit() else None
        async with factory() as session:

            await session.execute(text(f"DELETE FROM sj_scheme_roles WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> Any:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            # Depending on schema format, id might be _id or id
            d_id = getattr(d, "_id", getattr(d, "id", None))
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> Any:
        rm = r._mapping
        out = {
            "_id": str(rm["id"]), 
            "externalId": rm["external_id"]
        }
        
        created_at = rm["created_at"]
        if created_at:
            out["createdAt"] = created_at.isoformat()
            
        updated_at = rm["updated_at"]
        if updated_at:
            out["updatedAt"] = updated_at.isoformat()

        out["name"] = rm["name"]
        out["description"] = rm["description"]
        out["discountType"] = rm["discount_type"]
        out["discountValue"] = rm["discount_value"]
        out["minOrderValue"] = rm["min_order_value"]
        out["validFrom"] = rm["valid_from"]
        out["validUntil"] = rm["valid_until"]
        out["isActive"] = bool(rm["is_active"]) if rm["is_active"] is not None else None
        out["code"] = rm["code"]
        for k, v in children.items():
            out[k] = v
            
        return SchemeInternal(**out)

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_applicableRoles = text(f"SELECT parent_id, role FROM sj_scheme_roles WHERE parent_id IN ({id_list})")
        res_applicableRoles = await session.execute(q_applicableRoles)
        rows_applicableRoles = res_applicableRoles.fetchall()

        for r in rows_applicableRoles:
            if "applicableRoles" not in c_map[r.parent_id]:
                c_map[r.parent_id]["applicableRoles"] = []
            c_map[r.parent_id]["applicableRoles"].append(r[1])

        return c_map

    async def _replace_children(self, session, row_id: int, data: Any):

        if hasattr(data, "applicableRoles") and getattr(data, "applicableRoles") is not None:
            await session.execute(text(f"DELETE FROM sj_scheme_roles WHERE parent_id = :id"), {"id": row_id})
            child_list = getattr(data, "applicableRoles") or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_scheme_roles (parent_id, role) VALUES (:id, :v)"), {"id": row_id, "v": item})
