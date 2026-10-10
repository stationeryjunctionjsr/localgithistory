from typing import Optional, Dict, List, Any, Union
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
        
    async def findById(self, id: Union[int, str]) -> Optional['SchemeInternal']:
        factory = self._factory()
        if not factory or not id:
            return None
        async with factory() as session:
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
            children_map = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, children_map.get(int(row.id), {}))

    async def findByCode(self, code: str) -> Optional['SchemeInternal']:
        factory = self._factory()
        if not factory or not code:
            return None
        async with factory() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE code = :code LIMIT 1")
            result = await session.execute(q, {"code": code})
            row = result.fetchone()
            if not row:
                return None
            children_map = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, children_map.get(int(row.id), {}))

    async def findOne(
        self,
        query: Optional[dict] = None,
        code: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional['SchemeInternal']:
        if code:
            return await self.findByCode(code)
        if query:
            if "code" in query and query["code"]:
                return await self.findByCode(query["code"])
            if "_id" in query or "id" in query:
                return await self.findById(query.get("_id") or query.get("id"))
            if "externalId" in query and query["externalId"]:
                return await self.findById(query["externalId"])
        results = await self.findAll(query=query, is_active=is_active)
        return results[0] if results else None

    async def findAll(
        self,
        query: Optional[dict] = None,
        is_active: Optional[bool] = None,
        code: Optional[str] = None,
    ) -> List['SchemeInternal']:
        if query:
            if is_active is None and "is_active" in query:
                is_active = query["is_active"]
            if code is None and "code" in query:
                code = query["code"]

        clauses = []
        params = {}
        if is_active is not None:
            clauses.append("is_active = :act")
            params["act"] = 1 if is_active else 0
        if code is not None:
            clauses.append("code = :code")
            params["code"] = code

        where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"

        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
            children_map = await self._fetch_children(session, [int(r.id) for r in rows])
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

    async def delete(self, id: Union[int, str]) -> bool:
        factory = self._factory()
        if not factory or not id:
            return False
        async with factory() as session:
            if str(id).isdigit():
                pk = int(id)
            else:
                res = await session.execute(
                    text(f"SELECT id FROM {self.TABLE} WHERE external_id = :eid"), {"eid": str(id)}
                )
                pk = res.scalar()
                if not pk:
                    return False

            await session.execute(text("DELETE FROM sj_scheme_roles WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(self, r, children: Dict) -> 'SchemeInternal':
        from app.models.daos_flat import SchemeInternal
        return SchemeInternal(
            id=str(r.id),
            external_id=r.external_id,
            name=r.name,
            description=r.description,
            discount_type=r.discount_type,
            discount_value=float(r.discount_value) if r.discount_value is not None else None,
            min_purchase_amount=float(r.min_order_value) if r.min_order_value is not None else None,
            valid_from=r.valid_from,
            valid_until=r.valid_until,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            code=r.code,
            applicable_roles=children.get("applicable_roles", []),
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

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
