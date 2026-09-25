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
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: str) -> Optional['SchemeInternal']:
        return await self.findOne({"_id": id})

    async def findOne(self, query=None, **kwargs) -> Optional['SchemeInternal']:
        if query:
            kwargs.update(query)
        if not kwargs:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params = {}
            
            query_map = {'name': 'name', 'description': 'description', 'discount_type': 'discount_type', 'discount_value': 'discount_value', 'min_purchase_amount': 'min_order_value', 'valid_from': 'valid_from', 'valid_until': 'valid_until', 'is_active': 'is_active', 'code': 'code'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            for k, v in kwargs.items():
                db_col = query_map[k] if k in query_map else k
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
            
    async def findAll(self, query: Optional[dict] = None) -> List['SchemeInternal']:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'name': 'name', 'description': 'description', 'discount_type': 'discount_type', 'discount_value': 'discount_value', 'min_purchase_amount': 'min_order_value', 'valid_from': 'valid_from', 'valid_until': 'valid_until', 'is_active': 'is_active', 'code': 'code'}
            query_map["_id"] = "id"
            query_map["externalId"] = "external_id"
            
            if query:
                conditions = []
                for k, v in query.items():
                    db_col = query_map[k] if k in query_map else k
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

    async def create(self, data: 'SchemesInternalCreate') -> 'SchemeInternal':
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.name is not None:
            cols.append("name")
            params["s_name"] = data.name

        if data.description is not None:
            cols.append("description")
            params["s_description"] = data.description

        if data.discount_type is not None:
            cols.append("discount_type")
            params["s_discount_type"] = data.discount_type

        if data.discount_value is not None:
            cols.append("discount_value")
            params["s_discount_value"] = data.discount_value

        if data.min_purchase_amount is not None:
            cols.append("min_order_value")
            params["s_min_purchase_amount"] = data.min_purchase_amount

        if data.valid_from is not None:
            cols.append("valid_from")
            params["s_valid_from"] = data.valid_from

        if data.valid_until is not None:
            cols.append("valid_until")
            params["s_valid_until"] = data.valid_until

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = data.is_active

        if data.code is not None:
            cols.append("code")
            params["s_code"] = data.code

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['name', 'description', 'discount_type', 'discount_value', 'min_purchase_amount', 'valid_from', 'valid_until', 'is_active', 'code'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

    async def update(self, id: str, update_data: 'SchemesInternalUpdate') -> 'SchemeInternal':
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}

        if data.name is not None:
            updates.append("name = :s_name")
            params["s_name"] = data.name

        if data.description is not None:
            updates.append("description = :s_description")
            params["s_description"] = data.description

        if data.discount_type is not None:
            updates.append("discount_type = :s_discountType")
            params["s_discount_type"] = data.discount_type

        if data.discount_value is not None:
            updates.append("discount_value = :s_discountValue")
            params["s_discount_value"] = data.discount_value

        if data.min_purchase_amount is not None:
            updates.append("min_order_value = :s_minOrderValue")
            params["s_min_purchase_amount"] = data.min_purchase_amount

        if data.valid_from is not None:
            updates.append("valid_from = :s_validFrom")
            params["s_valid_from"] = data.valid_from

        if data.valid_until is not None:
            updates.append("valid_until = :s_validUntil")
            params["s_valid_until"] = data.valid_until

        if data.is_active is not None:
            updates.append("is_active = :s_isActive")
            params["s_is_active"] = data.is_active

        if data.code is not None:
            updates.append("code = :s_code")
            params["s_code"] = data.code

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

    async def deleteMany(self, query: Dict) -> 'SchemeInternal':
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            # Depending on schema format, id might be _id or id
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> 'SchemeInternal':
        d = dict(r._mapping)
        if "min_order_value" in d:
            d["min_purchase_amount"] = d.pop("min_order_value")
        if "applicable_roles" in children:
            d["applicable_roles"] = children["applicable_roles"]
        return SchemeInternal.model_validate(d)

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_applicableRoles = text(f"SELECT parent_id, role FROM sj_scheme_roles WHERE parent_id IN ({id_list})")
        res_applicableRoles = await session.execute(q_applicableRoles)
        rows_applicableRoles = res_applicableRoles.fetchall()

        for r in rows_applicableRoles:
            if "applicable_roles" not in c_map[r.parent_id]:
                c_map[r.parent_id]["applicable_roles"] = []
            c_map[r.parent_id]["applicable_roles"].append(r[1])

        return c_map

    async def _replace_children(self, session, row_id: int, data: 'CamelBaseModel'):

        if data.applicable_roles is not None:
            await session.execute(text(f"DELETE FROM sj_scheme_roles WHERE parent_id = :id"), {"id": row_id})
            child_list = data.applicable_roles or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_scheme_roles (parent_id, role) VALUES (:id, :v)"), {"id": row_id, "v": item})
