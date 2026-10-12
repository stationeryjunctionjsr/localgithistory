from typing import Optional, List, Union, Tuple
from datetime import datetime, timezone
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import DeliveryZoneInternal, DeliveryZoneInternalCreate, DeliveryZoneInternalUpdate, DeliveryChargeTierInternal

def now_utc():
    return datetime.now(timezone.utc)

def _parse_tier_row(r) -> DeliveryChargeTierInternal:
    max_val = (
        float('inf')
        if str(r.max_order_value).lower() in ("infinity", "inf")
        else (float(r.max_order_value) if str(r.max_order_value).replace('.', '', 1).isdigit() else r.max_order_value)
    )
    return DeliveryChargeTierInternal(
        min=float(r.min_order_value) if r.min_order_value and str(r.min_order_value).replace('.', '', 1).isdigit() else 0.0,
        max=max_val,
        charge=float(r.charge) if r.charge and str(r.charge).replace('.', '', 1).isdigit() else 0.0,
    )

class MySQLDeliveryZonesDAO:
    def __init__(self):
        self.table_name = "sj_delivery_zones"
    
    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional[DeliveryZoneInternal]:
        factory = self._factory()
        if not factory or not id:
            return None
        async with factory() as session:
            if not str(id).isdigit():
                return None
            q = text(f"SELECT * FROM {self.TABLE} WHERE id = :id LIMIT 1")
            params = {"id": int(id)}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            pincodes, tiers = await self._fetch_zone_children(session, int(row.id))
            return self._map_to_schema(
                row,
                pincodes=pincodes,
                tiers=tiers,
            )

    async def findByPincode(self, pincode: str, is_active: bool = True) -> Optional[DeliveryZoneInternal]:
        factory = self._factory()
        if not factory or not pincode:
            return None
        async with factory() as session:
            q = text(f"""
                SELECT z.* FROM {self.TABLE} z
                JOIN sj_delivery_zone_pincodes p ON z.id = p.parent_id
                WHERE p.pincode = :pincode AND z.is_active = :act
                LIMIT 1
            """)
            result = await session.execute(q, {"pincode": str(pincode), "act": 1 if is_active else 0})
            row = result.fetchone()
            if not row:
                return None
            pincodes, tiers = await self._fetch_zone_children(session, int(row.id))
            return self._map_to_schema(
                row,
                pincodes=pincodes,
                tiers=tiers,
            )
            
    async def findAll(self, is_active: Optional[bool] = None) -> List[DeliveryZoneInternal]:
        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
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
            pins_res = await session.execute(
                text(f"SELECT parent_id, pincode FROM sj_delivery_zone_pincodes WHERE parent_id IN ({id_list}) ORDER BY id ASC")
            )
            all_pin_rows = pins_res.fetchall()

            tiers_res = await session.execute(
                text(f"SELECT parent_id, min_order_value, max_order_value, charge FROM sj_delivery_zone_tiers WHERE parent_id IN ({id_list}) ORDER BY id ASC")
            )
            all_tier_rows = tiers_res.fetchall()

            return [
                self._map_to_schema(
                    r,
                    pincodes=[
                        str(pr.pincode)
                        for pr in all_pin_rows
                        if pr.parent_id == r.id
                    ],
                    tiers=[
                        _parse_tier_row(tr)
                        for tr in all_tier_rows
                        if tr.parent_id == r.id
                    ],
                )
                for r in rows
            ]

    async def create(self, data: DeliveryZoneInternalCreate) -> DeliveryZoneInternal:
        factory = self._factory()
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        params = {"c": now, "u": now}

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
        val_sql = ", ".join([f":{k}" for k in params.keys()])
        
        async with factory() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(str(new_id))

    async def update(self, id: Union[int, str], update_data: DeliveryZoneInternalUpdate) -> Optional[DeliveryZoneInternal]:
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
            updates.append("default_capacity = :s_default_capacity")
            params["s_default_capacity"] = data.default_capacity

        if data.urgent_delivery_available is not None:
            updates.append("urgent_delivery_available = :s_urgent_delivery_available")
            params["s_urgent_delivery_available"] = data.urgent_delivery_available

        if data.customer_type is not None:
            updates.append("customer_type = :s_customer_type")
            params["s_customer_type"] = data.customer_type

        if data.is_active is not None:
            updates.append("is_active = :s_is_active")
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

        async with factory() as session:
            if not str(id).isdigit():
                return None
            pk = int(id)
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
            if not str(id).isdigit():
                return False
            pk = int(id)

            await session.execute(text("DELETE FROM sj_delivery_zone_pincodes WHERE parent_id = :id"), {"id": pk})
            await session.execute(text("DELETE FROM sj_delivery_zone_tiers WHERE parent_id = :id"), {"id": pk})
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pk})
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(
        self,
        r,
        pincodes: List[str],
        tiers: List[DeliveryChargeTierInternal],
    ) -> DeliveryZoneInternal:
        return DeliveryZoneInternal(
            id=str(r.id),
            name=r.name,
            description=r.description,
            default_capacity=r.default_capacity,
            urgent_delivery_available=bool(r.urgent_delivery_available) if r.urgent_delivery_available is not None else None,
            customer_type=r.customer_type,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            delivery_charge=float(r.delivery_charge) if r.delivery_charge is not None else None,
            min_cart_value=float(r.min_cart_value) if r.min_cart_value is not None else None,
            urgent_delivery_charge=float(r.urgent_delivery_charge) if r.urgent_delivery_charge is not None else None,
            apply_default_charge=bool(r.apply_default_charge) if r.apply_default_charge is not None else True,
            pincodes=pincodes,
            tiers=tiers,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_zone_children(
        self, session, parent_id: int
    ) -> Tuple[List[str], List[DeliveryChargeTierInternal]]:
        q_pins = text("SELECT pincode FROM sj_delivery_zone_pincodes WHERE parent_id = :pid ORDER BY id ASC")
        res_pins = await session.execute(q_pins, {"pid": parent_id})
        pincodes = [str(r.pincode) for r in res_pins.fetchall()]

        q_tiers = text("SELECT min_order_value, max_order_value, charge FROM sj_delivery_zone_tiers WHERE parent_id = :pid ORDER BY id ASC")
        res_tiers = await session.execute(q_tiers, {"pid": parent_id})
        tiers = [_parse_tier_row(r) for r in res_tiers.fetchall()]

        return pincodes, tiers

    async def _replace_children(self, session, row_id: int, data: Union[DeliveryZoneInternalCreate, DeliveryZoneInternalUpdate]):
        if data.pincodes is not None:
            await session.execute(text("DELETE FROM sj_delivery_zone_pincodes WHERE parent_id = :id"), {"id": row_id})
            if data.pincodes:
                pin_params = [{"parent_id": row_id, "pincode": str(item)} for item in data.pincodes]
                await session.execute(
                    text("INSERT INTO sj_delivery_zone_pincodes (parent_id, pincode) VALUES (:parent_id, :pincode)"),
                    pin_params,
                )

        if data.tiers is not None:
            await session.execute(text("DELETE FROM sj_delivery_zone_tiers WHERE parent_id = :id"), {"id": row_id})
            if data.tiers:
                tier_params = [
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
                        "INSERT INTO sj_delivery_zone_tiers (parent_id, min_order_value, max_order_value, charge) "
                        "VALUES (:parent_id, :min_order_value, :max_order_value, :charge)"
                    ),
                    tier_params,
                )
