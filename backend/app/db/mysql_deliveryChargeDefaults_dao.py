from typing import Optional, List
from app.models.base import CamelBaseModel
from datetime import datetime, timezone
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import DeliveryChargeDefaultInternal, DeliveryChargeDefaultInternalCreate, DeliveryChargeDefaultInternalUpdate, DeliveryChargeTierInternal

def now_utc():
    return datetime.now(timezone.utc)

def _parse_tier_row(r) -> DeliveryChargeTierInternal:
    max_val = (
        float('inf')
        if str(r.max_order_value).lower() in ("infinity", "inf")
        else (float(r.max_order_value) if r.max_order_value is not None else float('inf'))
    )
    return DeliveryChargeTierInternal(
        min=float(r.min_order_value) if r.min_order_value is not None else 0.0,
        max=max_val,
        charge=float(r.charge) if r.charge is not None else 0.0,
    )

class MySQLDeliveryChargeDefaultsDAO:
    def __init__(self):
        self.table_name = "sj_delivery_charge_defaults"
    
    @property
    def TABLE(self):
        return self.table_name

    async def getDefault(self) -> Optional[DeliveryChargeDefaultInternal]:
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
            result = await session.execute(q)
            row = result.fetchone()
            if not row:
                return None
            tiers = await self._fetch_tiers(session, int(row.id))
            return self._map_to_schema(row, tiers)
        
    async def findById(self, id: int) -> Optional[DeliveryChargeDefaultInternal]:
        if not id:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            params = {"id": id}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            tiers = await self._fetch_tiers(session, row.id)
            return self._map_to_schema(row, tiers)
            
    async def findAll(self, is_active: Optional[bool] = None) -> List[DeliveryChargeDefaultInternal]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            if is_active is not None:
                sql = f"SELECT * FROM {self.TABLE} WHERE is_active = :act ORDER BY id ASC"
                params = {"act": 1 if is_active else 0}
            else:
                sql = f"SELECT * FROM {self.TABLE} ORDER BY id ASC"
                params = {}

            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
                
            parent_ids = [int(r.id) for r in rows]
            id_list = ",".join(str(i) for i in parent_ids)
            tiers_res = await session.execute(
                text(f"SELECT parent_id, min_order_value, max_order_value, charge FROM sj_delivery_charge_def_tiers WHERE parent_id IN ({id_list}) ORDER BY id ASC")
            )
            all_tier_rows = tiers_res.fetchall()
            return [
                self._map_to_schema(
                    r,
                    tiers=[
                        _parse_tier_row(tr)
                        for tr in all_tier_rows
                        if tr.parent_id == r.id
                    ],
                )
                for r in rows
            ]

    async def create(self, data: DeliveryChargeDefaultInternalCreate) -> DeliveryChargeDefaultInternal:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database session factory unavailable")
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        params = {"c": now, "u": now}

        if data.applicable_to_wholesaler is not None:
            cols.append("applicable_to_wholesaler")
            params["s_applicable_to_wholesaler"] = 1 if data.applicable_to_wholesaler else 0

        if data.applicable_to_retailer is not None:
            cols.append("applicable_to_retailer")
            params["s_applicable_to_retailer"] = 1 if data.applicable_to_retailer else 0

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = 1 if data.is_active else 0

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
        
        async with async_session() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: DeliveryChargeDefaultInternalUpdate) -> Optional[DeliveryChargeDefaultInternal]:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return None

        fields = update_data.model_fields_set
        if not fields:
            return await self.findById(id)

        updates = ["updated_at = :u"]
        params = {"pk": id, "u": now_utc()}
        data = update_data

        if "applicable_to_wholesaler" in fields:
            updates.append("applicable_to_wholesaler = :s_applicable_to_wholesaler")
            params["s_applicable_to_wholesaler"] = 1 if data.applicable_to_wholesaler else 0

        if "applicable_to_retailer" in fields:
            updates.append("applicable_to_retailer = :s_applicable_to_retailer")
            params["s_applicable_to_retailer"] = 1 if data.applicable_to_retailer else 0

        if "is_active" in fields:
            updates.append("is_active = :s_is_active")
            params["s_is_active"] = 1 if data.is_active else 0

        if "courier_base_charge" in fields:
            updates.append("courier_base_charge = :s_courier_base_charge")
            params["s_courier_base_charge"] = data.courier_base_charge

        if "courier_free_threshold" in fields:
            updates.append("courier_free_threshold = :s_courier_free_threshold")
            params["s_courier_free_threshold"] = data.courier_free_threshold

        if "hyperlocal_base_charge" in fields:
            updates.append("hyperlocal_base_charge = :s_hyperlocal_base_charge")
            params["s_hyperlocal_base_charge"] = data.hyperlocal_base_charge

        if "hyperlocal_free_threshold" in fields:
            updates.append("hyperlocal_free_threshold = :s_hyperlocal_free_threshold")
            params["s_hyperlocal_free_threshold"] = data.hyperlocal_free_threshold

        if "hyperlocal_urgent_delivery_charge" in fields:
            updates.append("hyperlocal_urgent_delivery_charge = :s_hyperlocal_urgent_delivery_charge")
            params["s_hyperlocal_urgent_delivery_charge"] = data.hyperlocal_urgent_delivery_charge

        upd_sql = ", ".join(updates)
        async with async_session() as session:
            await session.execute(text(f"UPDATE {self.TABLE} SET {upd_sql} WHERE id = :pk"), params)
            await self._replace_children(session, id, data)
            await session.commit()
                
        return await self.findById(id)

    async def delete(self, id: int) -> bool:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return False
        async with async_session() as session:
            pk = id

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
            id=r.id,
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

    async def _fetch_tiers(self, session, parent_id: int) -> List[DeliveryChargeTierInternal]:
        q_tiers = text("SELECT min_order_value, max_order_value, charge FROM sj_delivery_charge_def_tiers WHERE parent_id = :pid ORDER BY id ASC")
        res_tiers = await session.execute(q_tiers, {"pid": parent_id})
        return [_parse_tier_row(r) for r in res_tiers.fetchall()]

    async def _replace_children(self, session, row_id: int, data: CamelBaseModel):
        fields = data.model_fields_set
        if "tiers" in fields and data.tiers is not None:
            await session.execute(
                text("DELETE FROM sj_delivery_charge_def_tiers WHERE parent_id = :id"),
                {"id": row_id}
            )
            if data.tiers:
                params = [
                    {
                        "parent_id": row_id,
                        "min_order_value": str(tier.min if tier.min is not None else 0.0),
                        "max_order_value": "Infinity" if tier.max is None or tier.max == float("inf") else str(tier.max),
                        "charge": str(tier.charge if tier.charge is not None else 0.0),
                    }
                    for tier in data.tiers
                ]
                await session.execute(
                    text(
                        "INSERT INTO sj_delivery_charge_def_tiers (parent_id, min_order_value, max_order_value, charge) "
                        "VALUES (:parent_id, :min_order_value, :max_order_value, :charge)"
                    ),
                    params,
                )
