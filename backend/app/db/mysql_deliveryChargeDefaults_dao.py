import logging
from typing import List, Optional, Any
from app.db.mysql_connection import get_mysql_pool

# Assuming these models exist as requested
# from app.models.deliveryChargeDefaults import DeliveryChargeDefaultCreate, DeliveryChargeDefaultUpdate, DeliveryChargeDefaultResponse, DeliveryChargeDefTier

class MySQLDeliverychargedefaultsDAO:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def create(self, data: Any) -> Any:
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Insert parent
                insert_sql = """
                    INSERT INTO sj_delivery_charge_defaults 
                    (applicable_to_wholesaler, applicable_to_retailer, is_active) 
                    VALUES (%s, %s, %s)
                """
                await cursor.execute(insert_sql, (
                    data.applicableToWholesaler,
                    data.applicableToRetailer,
                    data.isActive
                ))
                parent_id = cursor.lastrowid

                # Insert child tiers
                if data.tiers:
                    tier_sql = """
                        INSERT INTO sj_delivery_charge_def_tiers 
                        (delivery_charge_default_id, min_order_value, max_order_value, charge) 
                        VALUES (%s, %s, %s, %s)
                    """
                    tier_values = []
                    for tier in data.tiers:
                        tier_values.append((
                            parent_id,
                            tier.min,
                            tier.max,
                            tier.charge
                        ))
                    await cursor.executemany(tier_sql, tier_values)

                await conn.commit()
                return await self.findById(parent_id)

    async def update(self, id: str, data: Any) -> Optional[Any]:
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Update parent
                update_sql = """
                    UPDATE sj_delivery_charge_defaults 
                    SET applicable_to_wholesaler = %s, applicable_to_retailer = %s, is_active = %s
                    WHERE id = %s
                """
                await cursor.execute(update_sql, (
                    data.applicableToWholesaler,
                    data.applicableToRetailer,
                    data.isActive,
                    id
                ))

                # Update child tiers
                if data.tiers is not None:
                    # Delete existing tiers
                    delete_tier_sql = "DELETE FROM sj_delivery_charge_def_tiers WHERE delivery_charge_default_id = %s"
                    await cursor.execute(delete_tier_sql, (id,))
                    
                    # Insert new tiers
                    if data.tiers:
                        tier_sql = """
                            INSERT INTO sj_delivery_charge_def_tiers 
                            (delivery_charge_default_id, min_order_value, max_order_value, charge) 
                            VALUES (%s, %s, %s, %s)
                        """
                        tier_values = []
                        for tier in data.tiers:
                            tier_values.append((
                                id,
                                tier.min,
                                tier.max,
                                tier.charge
                            ))
                        await cursor.executemany(tier_sql, tier_values)

                await conn.commit()
                return await self.findById(id)

    async def findById(self, id: str) -> Optional[Any]:
        from app.models.schemas import DeliveryChargeDefaultResponse, DeliveryChargeDefTier
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            from aiomysql import DictCursor
            async with conn.cursor(DictCursor) as cursor:
                sql = "SELECT id, applicable_to_wholesaler, applicable_to_retailer, is_active FROM sj_delivery_charge_defaults WHERE id = %s"
                await cursor.execute(sql, (id,))
                row = await cursor.fetchone()
                
                if not row:
                    return None
                    
                # Fetch tiers
                tier_sql = "SELECT min_order_value, max_order_value, charge FROM sj_delivery_charge_def_tiers WHERE delivery_charge_default_id = %s"
                await cursor.execute(tier_sql, (id,))
                tier_rows = await cursor.fetchall()
                
                tiers = []
                for tr in tier_rows:
                    tiers.append(DeliveryChargeDefTier(
                        min=tr['min_order_value'],
                        max=tr['max_order_value'],
                        charge=tr['charge']
                    ))
                    
                return DeliveryChargeDefaultResponse(
                    id=str(row['id']),
                    applicableToWholesaler=bool(row['applicable_to_wholesaler']),
                    applicableToRetailer=bool(row['applicable_to_retailer']),
                    isActive=bool(row['is_active']),
                    tiers=tiers
                )

    async def findOne(self) -> Optional[Any]:
        from app.models.schemas import DeliveryChargeDefaultResponse, DeliveryChargeDefTier
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            from aiomysql import DictCursor
            async with conn.cursor(DictCursor) as cursor:
                sql = "SELECT id, applicable_to_wholesaler, applicable_to_retailer, is_active FROM sj_delivery_charge_defaults LIMIT 1"
                await cursor.execute(sql)
                row = await cursor.fetchone()
                
                if not row:
                    return None
                    
                parent_id = row['id']
                
                # Fetch tiers
                tier_sql = "SELECT min_order_value, max_order_value, charge FROM sj_delivery_charge_def_tiers WHERE delivery_charge_default_id = %s"
                await cursor.execute(tier_sql, (parent_id,))
                tier_rows = await cursor.fetchall()
                
                tiers = []
                for tr in tier_rows:
                    tiers.append(DeliveryChargeDefTier(
                        min=tr['min_order_value'],
                        max=tr['max_order_value'],
                        charge=tr['charge']
                    ))
                    
                return DeliveryChargeDefaultResponse(
                    id=str(row['id']),
                    applicableToWholesaler=bool(row['applicable_to_wholesaler']),
                    applicableToRetailer=bool(row['applicable_to_retailer']),
                    isActive=bool(row['is_active']),
                    tiers=tiers
                )

    async def findAll(self) -> List[Any]:
        from app.models.schemas import DeliveryChargeDefaultResponse, DeliveryChargeDefTier
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            from aiomysql import DictCursor
            async with conn.cursor(DictCursor) as cursor:
                sql = "SELECT id, applicable_to_wholesaler, applicable_to_retailer, is_active FROM sj_delivery_charge_defaults"
                await cursor.execute(sql)
                rows = await cursor.fetchall()
                
                results = []
                for row in rows:
                    parent_id = row['id']
                    
                    # Fetch tiers
                    tier_sql = "SELECT min_order_value, max_order_value, charge FROM sj_delivery_charge_def_tiers WHERE delivery_charge_default_id = %s"
                    await cursor.execute(tier_sql, (parent_id,))
                    tier_rows = await cursor.fetchall()
                    
                    tiers = []
                    for tr in tier_rows:
                        tiers.append(DeliveryChargeDefTier(
                            min=tr['min_order_value'],
                            max=tr['max_order_value'],
                            charge=tr['charge']
                        ))
                        
                    results.append(DeliveryChargeDefaultResponse(
                        id=str(row['id']),
                        applicableToWholesaler=bool(row['applicable_to_wholesaler']),
                        applicableToRetailer=bool(row['applicable_to_retailer']),
                        isActive=bool(row['is_active']),
                        tiers=tiers
                    ))
                    
                return results

    async def delete(self, id: str) -> bool:
        pool = await get_mysql_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Delete tiers first (assuming no CASCADE)
                delete_tier_sql = "DELETE FROM sj_delivery_charge_def_tiers WHERE delivery_charge_default_id = %s"
                await cursor.execute(delete_tier_sql, (id,))
                
                delete_sql = "DELETE FROM sj_delivery_charge_defaults WHERE id = %s"
                await cursor.execute(delete_sql, (id,))
                
                deleted = cursor.rowcount > 0
                await conn.commit()
                return deleted
