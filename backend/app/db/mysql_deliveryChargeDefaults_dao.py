from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone
import secrets
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import DeliveryChargeDefaultInternal, DeliveryChargeDefaultInternalCreate, DeliveryChargeDefaultInternalUpdate, DeliveryChargeTierInternal

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
        
    async def findById(self, id: str) -> Optional[DeliveryChargeDefaultInternal]:
        return await self.findOne({"_id": id})

    async def findOne(self, query: Optional[Dict] = None) -> Optional[DeliveryChargeDefaultInternal]:
        docs = await self.findAll(query)
        return docs[0] if docs else None
            
    async def findAll(self, query: Optional[dict] = None) -> List[DeliveryChargeDefaultInternal]:
        query = query or {}
        async with self._factory()() as session:
            sql = f"SELECT * FROM {self.TABLE}"
            params = {}
            
            query_map = {
                'applicable_to_wholesaler': 'applicable_to_wholesaler',
                'applicable_to_retailer': 'applicable_to_retailer',
                'is_active': 'is_active',
                'courier_base_charge': 'courier_base_charge',
                'courier_free_threshold': 'courier_free_threshold',
                'hyperlocal_base_charge': 'hyperlocal_base_charge',
                'hyperlocal_free_threshold': 'hyperlocal_free_threshold',
                'hyperlocal_urgent_delivery_charge': 'hyperlocal_urgent_delivery_charge',
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

    async def create(self, data: DeliveryChargeDefaultInternalCreate) -> DeliveryChargeDefaultInternal:
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

        if data.courier_base_charge is not None:
            cols.append("courier_base_charge")
            params["s_courier_base_charge"] = data.courier_base_charge

        if data.courier_free_threshold is not None:
            cols.append("courier_free_threshold")
            params["s_courier_free_threshold"] = data.courier_free_threshold

        if data.hyperlocal_base_charge is not None:
            cols.append("hyperlocal_base_charge")
            params["s_hyperlocal_base_charge"] = data.hyperlocal_base_charge

        if data.hyperlocal_free_threshold is not None:
            cols.append("hyperlocal_free_threshold")
            params["s_hyperlocal_free_threshold"] = data.hyperlocal_free_threshold

        if data.hyperlocal_urgent_delivery_charge is not None:
            cols.append("hyperlocal_urgent_delivery_charge")
            params["s_hyperlocal_urgent_delivery_charge"] = data.hyperlocal_urgent_delivery_charge

        col_sql = ", ".join(cols)
        val_sql = ", ".join([f":{k}" if k in ("eid", "c", "u") else f":{k}" for k in params.keys()])
        
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

    async def update(self, id: str, update_data: DeliveryChargeDefaultInternalUpdate) -> DeliveryChargeDefaultInternal:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}
        data = update_data

        if data.applicable_to_wholesaler is not None:
            updates.append("applicable_to_wholesaler = :s_applicable_to_wholesaler")
            params["s_applicable_to_wholesaler"] = data.applicable_to_wholesaler

        if data.applicable_to_retailer is not None:
            updates.append("applicable_to_retailer = :s_applicable_to_retailer")
            params["s_applicable_to_retailer"] = data.applicable_to_retailer

        if data.is_active is not None:
            updates.append("is_active = :s_is_active")
            params["s_is_active"] = data.is_active

        if data.courier_base_charge is not None:
            updates.append("courier_base_charge = :s_courier_base_charge")
            params["s_courier_base_charge"] = data.courier_base_charge

        if data.courier_free_threshold is not None:
            updates.append("courier_free_threshold = :s_courier_free_threshold")
            params["s_courier_free_threshold"] = data.courier_free_threshold

        if data.hyperlocal_base_charge is not None:
            updates.append("hyperlocal_base_charge = :s_hyperlocal_base_charge")
            params["s_hyperlocal_base_charge"] = data.hyperlocal_base_charge

        if data.hyperlocal_free_threshold is not None:
            updates.append("hyperlocal_free_threshold = :s_hyperlocal_free_threshold")
            params["s_hyperlocal_free_threshold"] = data.hyperlocal_free_threshold

        if data.hyperlocal_urgent_delivery_charge is not None:
            updates.append("hyperlocal_urgent_delivery_charge = :s_hyperlocal_urgent_delivery_charge")
            params["s_hyperlocal_urgent_delivery_charge"] = data.hyperlocal_urgent_delivery_charge

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

    async def deleteMany(self, query: Dict) -> Dict[str, int]:
        docs = await self.findAll(query)
        deleted = 0
        for d in docs:
            d_id = d.id
            if d_id and await self.delete(d_id):
                deleted += 1
        return {"deletedCount": deleted}

    def _map_to_schema(self, r, children: Dict) -> DeliveryChargeDefaultInternal:
        obj = DeliveryChargeDefaultInternal.model_validate(r)
        for k, v in children.items():
            setattr(obj, k, v)
        return obj

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
            max_val = float('inf') if str(r[2]).lower() in ("infinity", "inf") else (float(r[2]) if str(r[2]).replace('.','',1).isdigit() else r[2])
            c_map[r.parent_id]["tiers"].append(
                DeliveryChargeTierInternal(
                    min=float(r[1]) if r[1] and str(r[1]).replace('.','',1).isdigit() else 0.0,
                    max=max_val,
                    charge=float(r[3]) if r[3] and str(r[3]).replace('.','',1).isdigit() else 0.0
                )
            )

        return c_map

    async def _replace_children(self, session, row_id: int, data: Union[DeliveryChargeDefaultInternalCreate, DeliveryChargeDefaultInternalUpdate]):
        if data.tiers is not None:
            await session.execute(
                text("DELETE FROM sj_delivery_charge_def_tiers WHERE parent_id = :id"),
                {"id": row_id}
            )
            for tier in data.tiers:
                max_str = "Infinity" if tier.max is None or tier.max == float("inf") else str(tier.max)
                await session.execute(
                    text(
                        "INSERT INTO sj_delivery_charge_def_tiers (parent_id, min_order_value, max_order_value, charge) "
                        "VALUES (:parent_id, :min_order_value, :max_order_value, :charge)"
                    ),
                    {
                        "parent_id": row_id,
                        "min_order_value": str(tier.min if tier.min is not None else 0.0),
                        "max_order_value": max_str,
                        "charge": str(tier.charge if tier.charge is not None else 0.0),
                    }
                )
