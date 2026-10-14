from typing import Optional, List, Union
from datetime import datetime, timezone
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import DeliveryChargeInternal, DeliveryChargeInternalCreate, DeliveryChargeInternalUpdate, DeliveryChargeTierInternal

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

class MySQLDeliveryChargesDAO:
    def __init__(self):
        self.table_name = "sj_delivery_charges"
    
    @property
    def TABLE(self):
        return self.table_name

    async def getMaxLocationId(self) -> int:
        async_session = get_async_session_factory()
        if not async_session:
            return 0
        async with async_session() as session:
            res = await session.execute(text(f"SELECT COALESCE(MAX(location_id), 0) FROM {self.TABLE}"))
            val = res.scalar()
            return int(val) if val is not None else 0
        
    async def findById(self, id: int) -> Optional[DeliveryChargeInternal]:
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

    async def findByPincode(self, pincode: str, is_active: bool = True) -> Optional[DeliveryChargeInternal]:
        if not pincode:
            return None
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE pincode = :pincode AND is_active = :act LIMIT 1")
            result = await session.execute(q, {"pincode": str(pincode), "act": 1 if is_active else 0})
            row = result.fetchone()
            if not row:
                return None
            tiers = await self._fetch_tiers(session, int(row.id))
            return self._map_to_schema(row, tiers)

    async def findByLocation(self, state: str, district: str, city: Optional[str] = None, is_active: bool = True) -> Optional[DeliveryChargeInternal]:
        async_session = get_async_session_factory()
        if not async_session:
            return None
        async with async_session() as session:
            if city:
                q = text(f"""
                    SELECT * FROM {self.TABLE}
                    WHERE LOWER(state) = LOWER(:state)
                      AND LOWER(district) = LOWER(:district)
                      AND LOWER(city) = LOWER(:city)
                      AND (pincode IS NULL OR pincode = '')
                      AND is_active = :act
                    LIMIT 1
                """)
                params = {"state": state, "district": district, "city": city, "act": 1 if is_active else 0}
            else:
                q = text(f"""
                    SELECT * FROM {self.TABLE}
                    WHERE LOWER(state) = LOWER(:state)
                      AND LOWER(district) = LOWER(:district)
                      AND (pincode IS NULL OR pincode = '')
                      AND is_active = :act
                    LIMIT 1
                """)
                params = {"state": state, "district": district, "act": 1 if is_active else 0}
            result = await session.execute(q, params)
            row = result.fetchone()
            if not row:
                return None
            tiers = await self._fetch_tiers(session, int(row.id))
            return self._map_to_schema(row, tiers)
            
    async def findAll(
        self,
        is_active: Optional[bool] = None,
        pincode: Optional[str] = None
    ) -> List[DeliveryChargeInternal]:
        async_session = get_async_session_factory()
        if not async_session:
            return []
        async with async_session() as session:
            conditions = []
            params = {}
            if is_active is not None:
                conditions.append("is_active = :act")
                params["act"] = 1 if is_active else 0
            if pincode is not None:
                conditions.append("pincode = :pin")
                params["pin"] = str(pincode)

            where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""
            sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
                
            parent_ids = [int(r.id) for r in rows]
            id_list = ",".join(str(i) for i in parent_ids)
            tiers_res = await session.execute(
                text(f"SELECT parent_id, min_order_value, max_order_value, charge FROM sj_delivery_charge_tiers WHERE parent_id IN ({id_list}) ORDER BY id ASC")
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

    async def create(self, data: DeliveryChargeInternalCreate) -> DeliveryChargeInternal:
        async_session = get_async_session_factory()
        if not async_session:
            raise RuntimeError("Database session factory unavailable")
        now = now_utc()
        
        cols = ["created_at", "updated_at"]
        params = {"c": now, "u": now}

        if data.location_id is not None:
            cols.append("location_id")
            params["s_location_id"] = data.location_id

        if data.pincode is not None:
            cols.append("pincode")
            params["s_pincode"] = data.pincode

        if data.state is not None:
            cols.append("state")
            params["s_state"] = data.state

        if data.city is not None:
            cols.append("city")
            params["s_city"] = data.city

        if data.district is not None:
            cols.append("district")
            params["s_district"] = data.district

        if data.apply_default_charge is not None:
            cols.append("apply_default_charge")
            params["s_apply_default_charge"] = 1 if data.apply_default_charge else 0

        if data.charge is not None:
            cols.append("charge")
            params["s_charge"] = data.charge

        if data.min_cart_value is not None:
            cols.append("min_cart_value")
            params["s_min_cart_value"] = data.min_cart_value

        if data.serviceable_for_customer is not None:
            cols.append("serviceable_for_customer")
            params["s_serviceable_for_customer"] = 1 if data.serviceable_for_customer else 0

        if data.serviceable_for_wholesaler is not None:
            cols.append("serviceable_for_wholesaler")
            params["s_serviceable_for_wholesaler"] = 1 if data.serviceable_for_wholesaler else 0

        if data.is_active is not None:
            cols.append("is_active")
            params["s_is_active"] = 1 if data.is_active else 0

        if data.description is not None:
            cols.append("description")
            params["s_description"] = data.description

        if data.urgent_delivery_available is not None:
            cols.append("urgent_delivery_available")
            params["s_urgent_delivery_available"] = 1 if data.urgent_delivery_available else 0

        if data.urgent_delivery_charge is not None:
            cols.append("urgent_delivery_charge")
            params["s_urgent_delivery_charge"] = data.urgent_delivery_charge

        col_sql = ", ".join(cols)
        val_sql = ", ".join([f":{k}" for k in params.keys()])
        
        async with async_session() as session:
            result = await session.execute(text(f"INSERT INTO {self.TABLE} ({col_sql}) VALUES ({val_sql})"), params)
            new_id = result.lastrowid
            await self._replace_children(session, new_id, data)
            await session.commit()
            
        return await self.findById(new_id)

    async def update(self, id: int, update_data: DeliveryChargeInternalUpdate) -> Optional[DeliveryChargeInternal]:
        async_session = get_async_session_factory()
        if not async_session or not id:
            return None

        fields = update_data.model_fields_set
        if not fields:
            return await self.findById(id)

        updates = ["updated_at = :u"]
        params = {"pk": id, "u": now_utc()}
        data = update_data

        if "location_id" in fields:
            updates.append("location_id = :s_location_id")
            params["s_location_id"] = data.location_id

        if "pincode" in fields:
            updates.append("pincode = :s_pincode")
            params["s_pincode"] = data.pincode

        if "state" in fields:
            updates.append("state = :s_state")
            params["s_state"] = data.state

        if "city" in fields:
            updates.append("city = :s_city")
            params["s_city"] = data.city

        if "district" in fields:
            updates.append("district = :s_district")
            params["s_district"] = data.district

        if "apply_default_charge" in fields:
            updates.append("apply_default_charge = :s_apply_default_charge")
            params["s_apply_default_charge"] = 1 if data.apply_default_charge else 0

        if "charge" in fields:
            updates.append("charge = :s_charge")
            params["s_charge"] = data.charge

        if "min_cart_value" in fields:
            updates.append("min_cart_value = :s_min_cart_value")
            params["s_min_cart_value"] = data.min_cart_value

        if "serviceable_for_customer" in fields:
            updates.append("serviceable_for_customer = :s_serviceable_for_customer")
            params["s_serviceable_for_customer"] = 1 if data.serviceable_for_customer else 0

        if "serviceable_for_wholesaler" in fields:
            updates.append("serviceable_for_wholesaler = :s_serviceable_for_wholesaler")
            params["s_serviceable_for_wholesaler"] = 1 if data.serviceable_for_wholesaler else 0

        if "is_active" in fields:
            updates.append("is_active = :s_is_active")
            params["s_is_active"] = 1 if data.is_active else 0

        if "description" in fields:
            updates.append("description = :s_description")
            params["s_description"] = data.description

        if "urgent_delivery_available" in fields:
            updates.append("urgent_delivery_available = :s_urgent_delivery_available")
            params["s_urgent_delivery_available"] = 1 if data.urgent_delivery_available else 0

        if "urgent_delivery_charge" in fields:
            updates.append("urgent_delivery_charge = :s_urgent_delivery_charge")
            params["s_urgent_delivery_charge"] = data.urgent_delivery_charge

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

            await session.execute(text("DELETE FROM sj_delivery_charge_tiers WHERE parent_id = :id"), {"id": pk})
            result = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE id = :id"), {"id": pk})
            await session.commit()
            return result.rowcount > 0

    def _map_to_schema(
        self,
        r,
        tiers: List[DeliveryChargeTierInternal],
    ) -> DeliveryChargeInternal:
        return DeliveryChargeInternal(
            id=r.id,
            location_id=r.location_id,
            pincode=r.pincode,
            state=r.state,
            city=r.city,
            district=r.district,
            apply_default_charge=bool(r.apply_default_charge) if r.apply_default_charge is not None else None,
            charge=float(r.charge) if r.charge is not None else None,
            min_cart_value=float(r.min_cart_value) if r.min_cart_value is not None else None,
            serviceable_for_customer=bool(r.serviceable_for_customer) if r.serviceable_for_customer is not None else None,
            serviceable_for_wholesaler=bool(r.serviceable_for_wholesaler) if r.serviceable_for_wholesaler is not None else None,
            is_active=bool(r.is_active) if r.is_active is not None else None,
            description=r.description,
            urgent_delivery_available=bool(r.urgent_delivery_available) if r.urgent_delivery_available is not None else None,
            urgent_delivery_charge=float(r.urgent_delivery_charge) if r.urgent_delivery_charge is not None else None,
            tiers=tiers,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    async def _fetch_tiers(self, session, parent_id: int) -> List[DeliveryChargeTierInternal]:
        q_tiers = text("SELECT min_order_value, max_order_value, charge FROM sj_delivery_charge_tiers WHERE parent_id = :pid ORDER BY id ASC")
        res_tiers = await session.execute(q_tiers, {"pid": parent_id})
        return [_parse_tier_row(r) for r in res_tiers.fetchall()]

    async def _replace_children(self, session, row_id: int, data: Union[DeliveryChargeInternalCreate, DeliveryChargeInternalUpdate]):
        fields = data.model_fields_set
        if "tiers" in fields and data.tiers is not None:
            await session.execute(
                text("DELETE FROM sj_delivery_charge_tiers WHERE parent_id = :id"),
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
                        "INSERT INTO sj_delivery_charge_tiers (parent_id, min_order_value, max_order_value, charge) "
                        "VALUES (:parent_id, :min_order_value, :max_order_value, :charge)"
                    ),
                    params,
                )
