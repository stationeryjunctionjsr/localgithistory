from typing import Optional, Dict, List, Any, Union
from collections import defaultdict
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
        return self.table_name

    def _factory(self):
        return get_async_session_factory()

    async def getDefault(self) -> Optional[DeliveryChargeDefaultInternal]:
        factory = self._factory()
        if not factory:
            return None
        async with factory() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
            result = await session.execute(q)
            row = result.fetchone()
            if not row:
                return None
            tiers_by_default = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, tiers_by_default.get(int(row.id), []))
        
    async def findById(self, id: Union[int, str]) -> Optional[DeliveryChargeDefaultInternal]:
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
            tiers_by_default = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, tiers_by_default.get(int(row.id), []))
            
    async def findAll(self, filter_or_active: Optional[Union[dict, bool]] = None, is_active: Optional[bool] = None) -> List[DeliveryChargeDefaultInternal]:
        active_filter = is_active
        if active_filter is None and filter_or_active is not None:
            if isinstance(filter_or_active, bool):
                active_filter = filter_or_active
            elif isinstance(filter_or_active, dict):
                active_filter = filter_or_active.get("is_active")

        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            if active_filter is not None:
                sql = f"SELECT * FROM {self.TABLE} WHERE is_active = :act ORDER BY id ASC"
                params = {"act": 1 if active_filter else 0}
            else:
                sql = f"SELECT * FROM {self.TABLE} ORDER BY id ASC"
                params = {}

            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
                
            tiers_by_default = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, tiers_by_default.get(int(r.id), [])) for r in rows]

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
        val_sql = ", ".join([f":{k}" for k in params.keys()])
        
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

    async def update(self, id: Union[int, str], update_data: DeliveryChargeDefaultInternalUpdate) -> Optional[DeliveryChargeDefaultInternal]:
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

        async with factory() as session:
            # Resolve numeric PK if external_id was passed
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

            if len(updates) > 1:
                upd_sql = ", ".join(updates)
                await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE {upd_where}"), params)

            await self._replace_children(session, pk, data)
            await session.commit()
                
        return await self.findById(str(pk))

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

            await session.execute(text("DELETE FROM sj_delivery_charge_def_tiers WHERE parent_id = :id"), {"id": pk})
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pk})
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(
        self,
        r,
        tiers: List[DeliveryChargeTierInternal],
    ) -> DeliveryChargeDefaultInternal:
        return DeliveryChargeDefaultInternal(
            id=str(r.id),
            external_id=r.external_id,
            applicable_to_wholesaler=bool(r.applicable_to_wholesaler) if r.applicable_to_wholesaler is not None else None,
            applicable_to_retailer=bool(r.applicable_to_retailer) if r.applicable_to_retailer is not None else None,
            charge=float(r.charge) if r.charge is not None else None,
            urgent_delivery_available=bool(r.urgent_delivery_available) if r.urgent_delivery_available is not None else None,
            urgent_delivery_charge=float(r.urgent_delivery_charge) if r.urgent_delivery_charge is not None else None,
            courier_base_charge=float(r.courier_base_charge) if r.courier_base_charge is not None else None,
            courier_free_threshold=float(r.courier_free_threshold) if r.courier_free_threshold is not None else None,
            hyperlocal_base_charge=float(r.hyperlocal_base_charge) if r.hyperlocal_base_charge is not None else None,
            hyperlocal_free_threshold=float(r.hyperlocal_free_threshold) if r.hyperlocal_free_threshold is not None else None,
            hyperlocal_urgent_delivery_charge=float(r.hyperlocal_urgent_delivery_charge) if r.hyperlocal_urgent_delivery_charge is not None else None,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            tiers=tiers,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, List[DeliveryChargeTierInternal]]:
        tiers_by_default: Dict[int, List[DeliveryChargeTierInternal]] = defaultdict(list)
        if not ids:
            return tiers_by_default
            
        id_list = ",".join(map(str, ids))

        q_tiers = text(f"SELECT parent_id, min_order_value, max_order_value, charge FROM sj_delivery_charge_def_tiers WHERE parent_id IN ({id_list})")
        res_tiers = await session.execute(q_tiers)
        for r in res_tiers.fetchall():
            max_val = (
                float('inf')
                if str(r.max_order_value).lower() in ("infinity", "inf")
                else (float(r.max_order_value) if str(r.max_order_value).replace('.', '', 1).isdigit() else r.max_order_value)
            )
            tiers_by_default[int(r.parent_id)].append(
                DeliveryChargeTierInternal(
                    min=float(r.min_order_value) if r.min_order_value and str(r.min_order_value).replace('.', '', 1).isdigit() else 0.0,
                    max=max_val,
                    charge=float(r.charge) if r.charge and str(r.charge).replace('.', '', 1).isdigit() else 0.0,
                )
            )

        return tiers_by_default

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
