from typing import List, Optional, Any, Dict
import aiomysql

# Note: Adjust the import below to match your actual models/schemas location
from app.models.delivery_zones import DeliveryZoneResponse

class MySQLDeliveryzonesDAO:
    def __init__(self, pool: aiomysql.Pool):
        self.pool = pool

    async def create(self, data) -> str:
        query = """
            INSERT INTO sj_delivery_zones (
                name, description, default_capacity, urgent_delivery_available, customer_type, is_active
            ) VALUES (
                %s, %s, %s, %s, %s, %s
            )
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (
                    data.name,
                    data.description,
                    data.defaultCapacity,
                    data.urgentDeliveryAvailable,
                    data.customerType,
                    data.isActive
                ))
                delivery_zone_id = cursor.lastrowid
                
                if data.pincodes is not None:
                    pincodes_query = "INSERT INTO sj_delivery_zone_pincodes (delivery_zone_id, pincode) VALUES (%s, %s)"
                    pincodes_data = [(delivery_zone_id, p) for p in data.pincodes]
                    if pincodes_data:
                        await cursor.executemany(pincodes_query, pincodes_data)
                    
                await conn.commit()
                return str(delivery_zone_id)
                
    async def update(self, id: str, data) -> bool:
        query = """
            UPDATE sj_delivery_zones SET
                name = %s,
                description = %s,
                default_capacity = %s,
                urgent_delivery_available = %s,
                customer_type = %s,
                is_active = %s
            WHERE id = %s
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (
                    data.name,
                    data.description,
                    data.defaultCapacity,
                    data.urgentDeliveryAvailable,
                    data.customerType,
                    data.isActive,
                    id
                ))
                
                # Delete existing pincodes
                await cursor.execute("DELETE FROM sj_delivery_zone_pincodes WHERE delivery_zone_id = %s", (id,))
                
                # Insert new pincodes
                if data.pincodes is not None:
                    pincodes_query = "INSERT INTO sj_delivery_zone_pincodes (delivery_zone_id, pincode) VALUES (%s, %s)"
                    pincodes_data = [(id, p) for p in data.pincodes]
                    if pincodes_data:
                        await cursor.executemany(pincodes_query, pincodes_data)
                    
                await conn.commit()
                return True

    async def _fetch_pincodes(self, cursor, delivery_zone_id: str) -> List[str]:
        await cursor.execute("SELECT pincode FROM sj_delivery_zone_pincodes WHERE delivery_zone_id = %s", (delivery_zone_id,))
        rows = await cursor.fetchall()
        return [row[0] for row in rows] if rows else []

    async def findById(self, id: str):
        query = """
            SELECT id, name, description, default_capacity, urgent_delivery_available, customer_type, is_active
            FROM sj_delivery_zones
            WHERE id = %s
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (id,))
                row = await cursor.fetchone()
                if not row:
                    return None
                    
                pincodes = await self._fetch_pincodes(cursor, row['id'])
                
                return DeliveryZoneResponse(
                    id=str(row['id']),
                    name=row['name'],
                    description=row['description'],
                    defaultCapacity=row['default_capacity'],
                    urgentDeliveryAvailable=bool(row['urgent_delivery_available']),
                    customerType=row['customer_type'],
                    isActive=bool(row['is_active']),
                    pincodes=pincodes
                )

    async def findOne(self, filters: dict):
        where_clauses = []
        params = []
        for k, v in filters.items():
            if k == 'name':
                where_clauses.append("name = %s")
            elif k == 'customerType':
                where_clauses.append("customer_type = %s")
            elif k == 'isActive':
                where_clauses.append("is_active = %s")
            elif k == 'urgentDeliveryAvailable':
                where_clauses.append("urgent_delivery_available = %s")
            elif k == 'defaultCapacity':
                where_clauses.append("default_capacity = %s")
            else:
                where_clauses.append(f"{k} = %s")
            params.append(v)
            
        where_str = " AND ".join(where_clauses) if where_clauses else "1=1"
        query = f"""
            SELECT id, name, description, default_capacity, urgent_delivery_available, customer_type, is_active
            FROM sj_delivery_zones
            WHERE {where_str}
            LIMIT 1
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, tuple(params))
                row = await cursor.fetchone()
                if not row:
                    return None
                    
                pincodes = await self._fetch_pincodes(cursor, row['id'])
                
                return DeliveryZoneResponse(
                    id=str(row['id']),
                    name=row['name'],
                    description=row['description'],
                    defaultCapacity=row['default_capacity'],
                    urgentDeliveryAvailable=bool(row['urgent_delivery_available']),
                    customerType=row['customer_type'],
                    isActive=bool(row['is_active']),
                    pincodes=pincodes
                )

    async def findAll(self, skip: int = 0, limit: int = 100):
        query = """
            SELECT id, name, description, default_capacity, urgent_delivery_available, customer_type, is_active
            FROM sj_delivery_zones
            LIMIT %s OFFSET %s
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (limit, skip))
                rows = await cursor.fetchall()
                
                result = []
                for row in rows:
                    pincodes = await self._fetch_pincodes(cursor, row['id'])
                    result.append(DeliveryZoneResponse(
                        id=str(row['id']),
                        name=row['name'],
                        description=row['description'],
                        defaultCapacity=row['default_capacity'],
                        urgentDeliveryAvailable=bool(row['urgent_delivery_available']),
                        customerType=row['customer_type'],
                        isActive=bool(row['is_active']),
                        pincodes=pincodes
                    ))
                return result
