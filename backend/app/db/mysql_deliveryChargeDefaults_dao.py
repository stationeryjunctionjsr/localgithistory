from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import DeliveryChargeDefaultInternal
from app.models.daos_flat import DeliveryChargeDefaultInternalCreate, DeliveryChargeDefaultInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLDeliveryChargeDefaultsDAO:
    def __init__(self):
        self.table_name = "sj_delivery_charge_defaults"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

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
            
            query_map = {'applicable_to_wholesaler': 'applicable_to_wholesaler', 'applicable_to_retailer': 'applicable_to_retailer', 'is_active': 'is_active'}
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
            
    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[Any]:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {'applicable_to_wholesaler': 'applicable_to_wholesaler', 'applicable_to_retailer': 'applicable_to_retailer', 'is_active': 'is_active'}
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

    async def create(self, data: Any) -> Any:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

        if data.applicable_to_wholesaler is not None:
            cols.append("applicable_to_wholesaler")
            params["s_applicable_to_wholesaler"] = data.applicable_to_wholesaler

        if data.applicable_to_retailer is not None:
            cols.append("applicable_to_retailer")
            params["s_applicable_to_retailer"] = data.applicable_to_retailer

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = data.is_active

        col_sql = ", ".join(cols)
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in ['applicable_to_wholesaler', 'applicable_to_retailer', 'is_active'] if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

        if data.applicable_to_wholesaler is not None:
            updates.append("applicable_to_wholesaler = :s_applicableToWholesaler")
            params["s_applicable_to_wholesaler"] = data.applicable_to_wholesaler

        if data.applicable_to_retailer is not None:
            updates.append("applicable_to_retailer = :s_applicableToRetailer")
            params["s_applicable_to_retailer"] = data.applicable_to_retailer

        if data.is_active is not None:
            updates.append("is_active = :s_isActive")
            params["s_is_active"] = data.is_active

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

            await session.execute(text(f"DELETE FROM sj_delivery_charge_def_tiers WHERE parent_id = :id"), {"id": pk})

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
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> Any:
        d = dict(r._mapping)
        d.update(children)
        return DeliveryChargeDefaultInternal.model_validate(d)

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_tiers = text(f"SELECT parent_id, min_order_value, max_order_value, charge FROM sj_delivery_charge_def_tiers WHERE parent_id IN ({id_list})")
        res_tiers = await session.execute(q_tiers)
        rows_tiers = res_tiers.fetchall()

        for r in rows_tiers:
            if "tiers" not in c_map[r.parent_id]:
                c_map[r.parent_id]["tiers"] = []
            obj = {}

            obj["min"] = r[1]
            obj["max"] = r[2]
            obj["charge"] = r[3]
            c_map[r.parent_id]["tiers"].append(obj)

        return c_map

    async def _replace_children(self, session, row_id: int, data: Any):

        if data.tiers is not None:
            await session.execute(text(f"DELETE FROM sj_delivery_charge_def_tiers WHERE parent_id = :id"), {"id": row_id})
            child_list = data.tiers or []

            if child_list:
                for item in child_list:
                    p = {"id": row_id}

                    p["v0"] = item.min
                    p["v1"] = item.max
                    p["v2"] = item.charge
                    await session.execute(text(f"INSERT INTO sj_delivery_charge_def_tiers (parent_id, min_order_value, max_order_value, charge) VALUES (:id, :v0, :v1, :v2)"), p)
