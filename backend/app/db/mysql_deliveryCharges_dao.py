import uuid
from typing import List, Optional, Any
from app.db.connection import get_db_connection
from app.schemas.deliveryCharges import (
    DeliveryChargeCreate,
    DeliveryChargeUpdate,
    DeliveryChargeResponse,
    DeliveryChargeTier
)

class MySQLDeliverychargesDAO:
    def __init__(self):
        pass

    def create(self, data: DeliveryChargeCreate) -> DeliveryChargeResponse:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                delivery_charge_id = str(uuid.uuid4())
                
                apply_default_charge = 1 if data.applyDefaultCharge else 0
                serviceable_for_customer = 1 if data.serviceableForCustomer else 0
                serviceable_for_retailer = 1 if data.serviceableForRetailer else 0
                serviceable_for_wholesaler = 1 if data.serviceableForWholesaler else 0
                is_active = 1 if data.isActive else 0

                sql = """
                    INSERT INTO sj_delivery_charges (
                        id, location_id, pincode, state, city, district, 
                        apply_default_charge, charge, min_cart_value, 
                        serviceable_for_customer, serviceable_for_retailer, 
                        serviceable_for_wholesaler, is_active, description
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                cursor.execute(sql, (
                    delivery_charge_id, data.locationId, data.pincode, data.state, 
                    data.city, data.district, apply_default_charge, data.charge, 
                    data.minCartValue, serviceable_for_customer, 
                    serviceable_for_retailer, serviceable_for_wholesaler, 
                    is_active, data.description
                ))

                if data.tiers:
                    for tier in data.tiers:
                        tier_id = str(uuid.uuid4())
                        tier_sql = """
                            INSERT INTO sj_delivery_charge_tiers (
                                id, delivery_charge_id, min_order_value, max_order_value, charge
                            ) VALUES (%s, %s, %s, %s, %s)
                        """
                        cursor.execute(tier_sql, (
                            tier_id, delivery_charge_id, tier.min, tier.max, tier.charge
                        ))
                
                conn.commit()
                return self.findById(delivery_charge_id)

    def update(self, delivery_charge_id: str, data: DeliveryChargeUpdate) -> Optional[DeliveryChargeResponse]:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                update_fields = []
                params = []

                if data.locationId is not None:
                    update_fields.append("location_id = %s")
                    params.append(data.locationId)
                if data.pincode is not None:
                    update_fields.append("pincode = %s")
                    params.append(data.pincode)
                if data.state is not None:
                    update_fields.append("state = %s")
                    params.append(data.state)
                if data.city is not None:
                    update_fields.append("city = %s")
                    params.append(data.city)
                if data.district is not None:
                    update_fields.append("district = %s")
                    params.append(data.district)
                if data.applyDefaultCharge is not None:
                    update_fields.append("apply_default_charge = %s")
                    params.append(1 if data.applyDefaultCharge else 0)
                if data.charge is not None:
                    update_fields.append("charge = %s")
                    params.append(data.charge)
                if data.minCartValue is not None:
                    update_fields.append("min_cart_value = %s")
                    params.append(data.minCartValue)
                if data.serviceableForCustomer is not None:
                    update_fields.append("serviceable_for_customer = %s")
                    params.append(1 if data.serviceableForCustomer else 0)
                if data.serviceableForRetailer is not None:
                    update_fields.append("serviceable_for_retailer = %s")
                    params.append(1 if data.serviceableForRetailer else 0)
                if data.serviceableForWholesaler is not None:
                    update_fields.append("serviceable_for_wholesaler = %s")
                    params.append(1 if data.serviceableForWholesaler else 0)
                if data.isActive is not None:
                    update_fields.append("is_active = %s")
                    params.append(1 if data.isActive else 0)
                if data.description is not None:
                    update_fields.append("description = %s")
                    params.append(data.description)

                if update_fields:
                    sql = f"UPDATE sj_delivery_charges SET {', '.join(update_fields)} WHERE id = %s"
                    params.append(delivery_charge_id)
                    cursor.execute(sql, tuple(params))

                if data.tiers is not None:
                    cursor.execute("DELETE FROM sj_delivery_charge_tiers WHERE delivery_charge_id = %s", (delivery_charge_id,))
                    for tier in data.tiers:
                        tier_id = str(uuid.uuid4())
                        tier_sql = """
                            INSERT INTO sj_delivery_charge_tiers (
                                id, delivery_charge_id, min_order_value, max_order_value, charge
                            ) VALUES (%s, %s, %s, %s, %s)
                        """
                        cursor.execute(tier_sql, (
                            tier_id, delivery_charge_id, tier.min, tier.max, tier.charge
                        ))
                
                conn.commit()
                return self.findById(delivery_charge_id)

    def findById(self, delivery_charge_id: str) -> Optional[DeliveryChargeResponse]:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                sql = "SELECT * FROM sj_delivery_charges WHERE id = %s"
                cursor.execute(sql, (delivery_charge_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                tier_sql = "SELECT * FROM sj_delivery_charge_tiers WHERE delivery_charge_id = %s"
                cursor.execute(tier_sql, (delivery_charge_id,))
                tiers_rows = cursor.fetchall()
                
                return self._map_to_response(row, tiers_rows)

    def findOne(self, filters: dict) -> Optional[DeliveryChargeResponse]:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                if not filters:
                    return None
                where_clauses = []
                params = []
                for k, v in filters.items():
                    where_clauses.append(f"{k} = %s")
                    params.append(v)
                sql = f"SELECT * FROM sj_delivery_charges WHERE {' AND '.join(where_clauses)} LIMIT 1"
                cursor.execute(sql, tuple(params))
                row = cursor.fetchone()
                if not row:
                    return None
                
                tier_sql = "SELECT * FROM sj_delivery_charge_tiers WHERE delivery_charge_id = %s"
                cursor.execute(tier_sql, (row['id'],))
                tiers_rows = cursor.fetchall()
                
                return self._map_to_response(row, tiers_rows)

    def findAll(self, skip: int = 0, limit: int = 100, filters: dict = None) -> List[DeliveryChargeResponse]:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                where_clauses = []
                params = []
                if filters:
                    for k, v in filters.items():
                        where_clauses.append(f"{k} = %s")
                        params.append(v)
                
                sql = "SELECT * FROM sj_delivery_charges"
                if where_clauses:
                    sql += " WHERE " + " AND ".join(where_clauses)
                sql += " LIMIT %s OFFSET %s"
                params.extend([limit, skip])
                
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()
                
                responses = []
                for row in rows:
                    tier_sql = "SELECT * FROM sj_delivery_charge_tiers WHERE delivery_charge_id = %s"
                    cursor.execute(tier_sql, (row['id'],))
                    tiers_rows = cursor.fetchall()
                    responses.append(self._map_to_response(row, tiers_rows))
                
                return responses

    def delete(self, delivery_charge_id: str) -> bool:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM sj_delivery_charge_tiers WHERE delivery_charge_id = %s", (delivery_charge_id,))
                cursor.execute("DELETE FROM sj_delivery_charges WHERE id = %s", (delivery_charge_id,))
                conn.commit()
                return cursor.rowcount > 0

    def _map_to_response(self, row: dict, tiers_rows: list) -> DeliveryChargeResponse:
        tiers = []
        if tiers_rows:
            for tier in tiers_rows:
                tiers.append(DeliveryChargeTier(
                    min=tier['min_order_value'],
                    max=tier['max_order_value'],
                    charge=tier['charge']
                ))
        
        return DeliveryChargeResponse(
            id=row['id'],
            locationId=(row['location_id'] if 'location_id' in row else None),
            pincode=(row['pincode'] if 'pincode' in row else None),
            state=(row['state'] if 'state' in row else None),
            city=(row['city'] if 'city' in row else None),
            district=(row['district'] if 'district' in row else None),
            applyDefaultCharge=bool((row['apply_default_charge'] if 'apply_default_charge' in row else None)),
            charge=(row['charge'] if 'charge' in row else None),
            minCartValue=(row['min_cart_value'] if 'min_cart_value' in row else None),
            serviceableForCustomer=bool((row['serviceable_for_customer'] if 'serviceable_for_customer' in row else None)),
            serviceableForRetailer=bool((row['serviceable_for_retailer'] if 'serviceable_for_retailer' in row else None)),
            serviceableForWholesaler=bool((row['serviceable_for_wholesaler'] if 'serviceable_for_wholesaler' in row else None)),
            isActive=bool((row['is_active'] if 'is_active' in row else None)),
            description=(row['description'] if 'description' in row else None),
            tiers=tiers,
            createdAt=(row['created_at'] if 'created_at' in row else None),
            updatedAt=(row['updated_at'] if 'updated_at' in row else None)
        )
