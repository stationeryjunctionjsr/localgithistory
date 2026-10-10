from typing import Optional, Dict, List, Any, Union
from collections import defaultdict
from datetime import datetime, timezone
import secrets
from sqlalchemy import text
from app.config.database import get_async_session_factory
from app.models.daos_flat import DeliveryChargeInternal, DeliveryChargeInternalCreate, DeliveryChargeInternalUpdate, DeliveryChargeTierInternal

def now_utc():
    return datetime.now(timezone.utc)

class MySQLDeliveryChargesDAO:
    def __init__(self):
        self.table_name = "sj_delivery_charges"
    
    @property
    def TABLE(self):
        return self.table_name

    def _factory(self):
        return get_async_session_factory()
        
    async def findById(self, id: Union[int, str]) -> Optional[DeliveryChargeInternal]:
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
            tiers_by_charge = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, tiers_by_charge.get(int(row.id), []))

    async def findByPincode(self, pincode: str, is_active: bool = True) -> Optional[DeliveryChargeInternal]:
        factory = self._factory()
        if not factory or not pincode:
            return None
        async with factory() as session:
            q = text(f"SELECT * FROM {self.TABLE} WHERE pincode = :pincode AND is_active = :act LIMIT 1")
            result = await session.execute(q, {"pincode": str(pincode), "act": 1 if is_active else 0})
            row = result.fetchone()
            if not row:
                return None
            tiers_by_charge = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, tiers_by_charge.get(int(row.id), []))

    async def findByLocation(self, state: str, district: str, city: Optional[str] = None, is_active: bool = True) -> Optional[DeliveryChargeInternal]:
        factory = self._factory()
        if not factory:
            return None
        async with factory() as session:
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
            tiers_by_charge = await self._fetch_children(session, [int(row.id)])
            return self._map_to_schema(row, tiers_by_charge.get(int(row.id), []))
            
    async def findAll(
        self,
        filter_or_active: Optional[Union[dict, bool]] = None,
        is_active: Optional[bool] = None,
        pincode: Optional[str] = None
    ) -> List[DeliveryChargeInternal]:
        active_filter = is_active
        pincode_filter = pincode
        if filter_or_active is not None:
            if isinstance(filter_or_active, bool):
                active_filter = filter_or_active
            elif isinstance(filter_or_active, dict):
                if "is_active" in filter_or_active:
                    active_filter = filter_or_active["is_active"]
                if "pincode" in filter_or_active:
                    pincode_filter = filter_or_active["pincode"]

        factory = self._factory()
        if not factory:
            return []
        async with factory() as session:
            conditions = []
            params = {}
            if active_filter is not None:
                conditions.append("is_active = :act")
                params["act"] = 1 if active_filter else 0
            if pincode_filter is not None:
                conditions.append("pincode = :pin")
                params["pin"] = str(pincode_filter)

            where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""
            sql = f"SELECT * FROM {self.TABLE}{where_sql} ORDER BY id ASC"
            result = await session.execute(text(sql), params)
            rows = result.fetchall()
            if not rows:
                return []
                
            tiers_by_charge = await self._fetch_children(session, [int(r.id) for r in rows])
            return [self._map_to_schema(r, tiers_by_charge.get(int(r.id), [])) for r in rows]

    async def create(self, data: DeliveryChargeInternalCreate) -> DeliveryChargeInternal:
        factory = self._factory()
        now = now_utc()
        external_id = secrets.token_hex(16)
        
        cols = ["external_id", "created_at", "updated_at"]
        params = {"eid": external_id, "c": now, "u": now}

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

    async def update(self, id: Union[int, str], update_data: DeliveryChargeInternalUpdate) -> Optional[DeliveryChargeInternal]:
        factory = self._factory()
        updates = ["updated_at = :u"]
        params = {"id": id, "u": now_utc()}
        data = update_data

        if data.location_id is not None:
            updates.append("location_id = :s_location_id")
            params["s_location_id"] = data.location_id

        if data.pincode is not None:
            updates.append("pincode = :s_pincode")
            params["s_pincode"] = data.pincode

        if data.state is not None:
            updates.append("state = :s_state")
            params["s_state"] = data.state

        if data.city is not None:
            updates.append("city = :s_city")
            params["s_city"] = data.city

        if data.district is not None:
            updates.append("district = :s_district")
            params["s_district"] = data.district

        if data.apply_default_charge is not None:
            updates.append("apply_default_charge = :s_apply_default_charge")
            params["s_apply_default_charge"] = 1 if data.apply_default_charge else 0

        if data.charge is not None:
            updates.append("charge = :s_charge")
            params["s_charge"] = data.charge

        if data.min_cart_value is not None:
            updates.append("min_cart_value = :s_min_cart_value")
            params["s_min_cart_value"] = data.min_cart_value

        if data.serviceable_for_customer is not None:
            updates.append("serviceable_for_customer = :s_serviceable_for_customer")
            params["s_serviceable_for_customer"] = 1 if data.serviceable_for_customer else 0

        if data.serviceable_for_wholesaler is not None:
            updates.append("serviceable_for_wholesaler = :s_serviceable_for_wholesaler")
            params["s_serviceable_for_wholesaler"] = 1 if data.serviceable_for_wholesaler else 0

        if data.is_active is not None:
            updates.append("is_active = :s_is_active")
            params["s_is_active"] = 1 if data.is_active else 0

        if data.description is not None:
            updates.append("description = :s_description")
            params["s_description"] = data.description

        if data.urgent_delivery_available is not None:
            updates.append("urgent_delivery_available = :s_urgent_delivery_available")
            params["s_urgent_delivery_available"] = 1 if data.urgent_delivery_available else 0

        if data.urgent_delivery_charge is not None:
            updates.append("urgent_delivery_charge = :s_urgent_delivery_charge")
            params["s_urgent_delivery_charge"] = data.urgent_delivery_charge

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
            id=str(r.id),
            external_id=r.external_id,
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

    async def _fetch_children(self, session, ids: List[int]) -> Dict[int, List[DeliveryChargeTierInternal]]:
        tiers_by_charge: Dict[int, List[DeliveryChargeTierInternal]] = defaultdict(list)
        if not ids:
            return tiers_by_charge
            
        id_list = ",".join(map(str, ids))

        q_tiers = text(f"SELECT parent_id, min_order_value, max_order_value, charge FROM sj_delivery_charge_tiers WHERE parent_id IN ({id_list})")
        res_tiers = await session.execute(q_tiers)
        for r in res_tiers.fetchall():
            max_val = (
                float('inf')
                if str(r.max_order_value).lower() in ("infinity", "inf")
                else (float(r.max_order_value) if str(r.max_order_value).replace('.', '', 1).isdigit() else r.max_order_value)
            )
            tiers_by_charge[int(r.parent_id)].append(
                DeliveryChargeTierInternal(
                    min=float(r.min_order_value) if r.min_order_value and str(r.min_order_value).replace('.', '', 1).isdigit() else 0.0,
                    max=max_val,
                    charge=float(r.charge) if r.charge and str(r.charge).replace('.', '', 1).isdigit() else 0.0,
                )
            )

        return tiers_by_charge

    async def _replace_children(self, session, row_id: int, data: Union[DeliveryChargeInternalCreate, DeliveryChargeInternalUpdate]):
        if data.tiers is not None:
            await session.execute(
                text("DELETE FROM sj_delivery_charge_tiers WHERE parent_id = :id"),
                {"id": row_id}
            )
            for tier in data.tiers:
                max_str = "Infinity" if tier.max is None or tier.max == float("inf") else str(tier.max)
                await session.execute(
                    text(
                        "INSERT INTO sj_delivery_charge_tiers (parent_id, min_order_value, max_order_value, charge) "
                        "VALUES (:parent_id, :min_order_value, :max_order_value, :charge)"
                    ),
                    {
                        "parent_id": row_id,
                        "min_order_value": str(tier.min if tier.min is not None else 0.0),
                        "max_order_value": max_str,
                        "charge": str(tier.charge if tier.charge is not None else 0.0),
                    }
                )
