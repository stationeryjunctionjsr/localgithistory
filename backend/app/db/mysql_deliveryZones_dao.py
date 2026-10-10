from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import secrets
import json
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import DeliveryZoneInternal
from app.models.daos_flat import DeliveryZoneInternalCreate, DeliveryZoneInternalUpdate

def now_utc():
    return datetime.now(timezone.utc)

class MySQLDeliveryZonesDAO:
    def __init__(self):
        self.table_name = "sj_delivery_zones"
    
    @property
    def TABLE(self):
        from app.config.settings import settings
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: str) -> Optional['DeliveryZoneInternal']:
        return await self.findOne({"_id": id})

    async def findOne(self, query=None, **kwargs) -> Optional['DeliveryZoneInternal']:
        if query:
            kwargs.update(query)
        if not kwargs:
            return None
        
        async with self._factory()() as session:
            conditions = []
            params = {}
            
            query_map = {
                'name': 'name', 'description': 'description', 'default_capacity': 'default_capacity',
                'urgent_delivery_available': 'urgent_delivery_available', 'customer_type': 'customer_type',
                'is_active': 'is_active', 'delivery_charge': 'delivery_charge', 'min_cart_value': 'min_cart_value',
                'urgent_delivery_charge': 'urgent_delivery_charge', 'apply_default_charge': 'apply_default_charge',
                'deliveryCharge': 'delivery_charge', 'minCartValue': 'min_cart_value',
                'urgentDeliveryCharge': 'urgent_delivery_charge', 'applyDefaultCharge': 'apply_default_charge'
            }
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
            
    async def findAll(self, query: Optional[dict] = None) -> List['DeliveryZoneInternal']:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {
                'name': 'name', 'description': 'description', 'default_capacity': 'default_capacity',
                'urgent_delivery_available': 'urgent_delivery_available', 'customer_type': 'customer_type',
                'is_active': 'is_active', 'delivery_charge': 'delivery_charge', 'min_cart_value': 'min_cart_value',
                'urgent_delivery_charge': 'urgent_delivery_charge', 'apply_default_charge': 'apply_default_charge',
                'deliveryCharge': 'delivery_charge', 'minCartValue': 'min_cart_value',
                'urgentDeliveryCharge': 'urgent_delivery_charge', 'applyDefaultCharge': 'apply_default_charge'
            }
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

    async def create(self, data: 'DeliveryZoneInternalCreate') -> 'DeliveryZoneInternal':
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

        if data.default_capacity is not None:
            cols.append("default_capacity")
            params["s_default_capacity"] = data.default_capacity

        if data.urgent_delivery_available is not None:
            cols.append("urgent_delivery_available")
            params["s_urgent_delivery_available"] = data.urgent_delivery_available

        if data.customer_type is not None:
            cols.append("customer_type")
            params["s_customer_type"] = data.customer_type

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = data.is_active

        if data.delivery_charge is not None:
            cols.append("delivery_charge")
            params["s_delivery_charge"] = data.delivery_charge

        if data.min_cart_value is not None:
            cols.append("min_cart_value")
            params["s_min_cart_value"] = data.min_cart_value

        if data.urgent_delivery_charge is not None:
            cols.append("urgent_delivery_charge")
            params["s_urgent_delivery_charge"] = data.urgent_delivery_charge

        if data.apply_default_charge is not None:
            cols.append("apply_default_charge")
            params["s_apply_default_charge"] = 1 if data.apply_default_charge else 0

        col_sql = ", ".join(cols)
        zone_keys = ['name', 'description', 'default_capacity', 'urgent_delivery_available', 'customer_type', 'is_active', 'delivery_charge', 'min_cart_value', 'urgent_delivery_charge', 'apply_default_charge']
        val_sql = ", ".join([":eid", ":c", ":u"] + [f":s_{k}" for k in zone_keys if f"s_{k}" in params] + [f":c_{k}" for k in [] if f"c_{k}" in params])
        
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

    async def update(self, id: str, update_data: 'DeliveryZoneInternalUpdate') -> 'DeliveryZoneInternal':
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}
        data = update_data

        if data.name is not None:
            updates.append("name = :s_name")
            params["s_name"] = data.name

        if data.description is not None:
            updates.append("description = :s_description")
            params["s_description"] = data.description

        if data.default_capacity is not None:
            updates.append("default_capacity = :s_defaultCapacity")
            params["s_default_capacity"] = data.default_capacity

        if data.urgent_delivery_available is not None:
            updates.append("urgent_delivery_available = :s_urgentDeliveryAvailable")
            params["s_urgent_delivery_available"] = data.urgent_delivery_available

        if data.customer_type is not None:
            updates.append("customer_type = :s_customerType")
            params["s_customer_type"] = data.customer_type

        if data.is_active is not None:
            updates.append("is_active = :s_isActive")
            params["s_is_active"] = data.is_active

        if data.delivery_charge is not None:
            updates.append("delivery_charge = :s_delivery_charge")
            params["s_delivery_charge"] = data.delivery_charge

        if data.min_cart_value is not None:
            updates.append("min_cart_value = :s_min_cart_value")
            params["s_min_cart_value"] = data.min_cart_value

        if data.urgent_delivery_charge is not None:
            updates.append("urgent_delivery_charge = :s_urgent_delivery_charge")
            params["s_urgent_delivery_charge"] = data.urgent_delivery_charge

        if data.apply_default_charge is not None:
            updates.append("apply_default_charge = :s_apply_default_charge")
            params["s_apply_default_charge"] = 1 if data.apply_default_charge else 0

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

            await session.execute(text(f"DELETE FROM sj_delivery_zone_pincodes WHERE parent_id = :id"), {"id": pk})
            await session.execute(text(f"DELETE FROM sj_delivery_zone_tiers WHERE parent_id = :id"), {"id": pk})

            result = await session.execute(
                text(f"DELETE FROM {self.TABLE} WHERE id = :id"),
                {"id": pk},
            )
            await session.commit()
            return result.rowcount > 0

    async def deleteMany(self, query: Dict) -> 'DeliveryZoneInternal':
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            # Depending on schema format, id might be _id or id
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> 'DeliveryZoneInternal':
        obj = DeliveryZoneInternal.model_validate(r)
        for k, v in children.items():
            setattr(obj, k, v)
        return obj

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, Dict]:
        c_map = {rid: {} for rid in ids}
        if not ids:
            return c_map
            
        id_list = ",".join(map(str, ids))

        q_pincodes = text(f"SELECT parent_id, pincode FROM sj_delivery_zone_pincodes WHERE parent_id IN ({id_list})")
        res_pincodes = await session.execute(q_pincodes)
        rows_pincodes = res_pincodes.fetchall()

        for r in rows_pincodes:
            if "pincodes" not in c_map[r.parent_id]:
                c_map[r.parent_id]["pincodes"] = []
            c_map[r.parent_id]["pincodes"].append(r[1])

        q_tiers = text(f"SELECT parent_id, min_order_value, max_order_value, charge FROM sj_delivery_zone_tiers WHERE parent_id IN ({id_list})")
        res_tiers = await session.execute(q_tiers)
        for r in res_tiers.fetchall():
            if "tiers" not in c_map[r.parent_id]:
                c_map[r.parent_id]["tiers"] = []
            max_val = "Infinity" if str(r.max_order_value).lower() in ("infinity", "inf") else (float(r.max_order_value) if str(r.max_order_value).replace('.','',1).isdigit() else r.max_order_value)
            c_map[r.parent_id]["tiers"].append({
                "min": float(r.min_order_value) if r.min_order_value and str(r.min_order_value).replace('.','',1).isdigit() else 0.0,
                "max": max_val,
                "charge": float(r.charge) if r.charge and str(r.charge).replace('.','',1).isdigit() else 0.0
            })

        return c_map

    async def _replace_children(self, session, row_id: int, data: 'CamelBaseModel'):

        if data.pincodes is not None:
            await session.execute(text(f"DELETE FROM sj_delivery_zone_pincodes WHERE parent_id = :id"), {"id": row_id})
            child_list = data.pincodes or []

            if child_list:
                for item in child_list:
                    await session.execute(text(f"INSERT INTO sj_delivery_zone_pincodes (parent_id, pincode) VALUES (:id, :v)"), {"id": row_id, "v": item})

        if hasattr(data, 'tiers') and data.tiers is not None:
            await session.execute(text(f"DELETE FROM sj_delivery_zone_tiers WHERE parent_id = :id"), {"id": row_id})
            child_tiers = data.tiers or []

            for tier in child_tiers:
                t_min = str(getattr(tier, 'min', None) if getattr(tier, 'min', None) is not None else (tier.get('min', '0') if isinstance(tier, dict) else '0'))
                t_max = str(getattr(tier, 'max', None) if getattr(tier, 'max', None) is not None else (tier.get('max', 'Infinity') if isinstance(tier, dict) else 'Infinity'))
                t_chg = str(getattr(tier, 'charge', None) if getattr(tier, 'charge', None) is not None else (tier.get('charge', '0') if isinstance(tier, dict) else '0'))
                await session.execute(
                    text("INSERT INTO sj_delivery_zone_tiers (parent_id, min_order_value, max_order_value, charge) VALUES (:id, :min_val, :max_val, :charge)"),
                    {"id": row_id, "min_val": t_min, "max_val": t_max, "charge": t_chg}
                )
