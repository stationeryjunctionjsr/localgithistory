import aiomysql
from typing import List, Optional, Dict, Any
from app.models.schemas import SchemeResponse # Adjust import path as needed

class MySQLSchemesDAO:
    def __init__(self, pool: aiomysql.Pool):
        self.pool = pool

    async def create(self, data) -> int:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                insert_query = """
                    INSERT INTO sj_schemes (
                        name, description, is_active, valid_from, valid_until, 
                        min_order_value, max_discount, discount_type, discount_value
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                await cursor.execute(
                    insert_query,
                    (
                        data.name,
                        data.description,
                        data.isActive,
                        data.validFrom,
                        data.validUntil,
                        data.minOrderValue,
                        data.maxDiscount,
                        data.discountType,
                        data.discountValue
                    )
                )
                scheme_id = cursor.lastrowid

                if data.applicableCategories is not None:
                    cat_query = "INSERT INTO sj_scheme_categories (scheme_id, category) VALUES (%s, %s)"
                    cat_values = [(scheme_id, cat) for cat in data.applicableCategories]
                    if cat_values:
                        await cursor.executemany(cat_query, cat_values)

                if data.applicableProducts is not None:
                    prod_query = "INSERT INTO sj_scheme_products (scheme_id, product_id) VALUES (%s, %s)"
                    prod_values = [(scheme_id, prod) for prod in data.applicableProducts]
                    if prod_values:
                        await cursor.executemany(prod_query, prod_values)

                if data.applicableRoles is not None:
                    role_query = "INSERT INTO sj_scheme_roles (scheme_id, role) VALUES (%s, %s)"
                    role_values = [(scheme_id, role) for role in data.applicableRoles]
                    if role_values:
                        await cursor.executemany(role_query, role_values)

                await conn.commit()
                return scheme_id

    async def update(self, scheme_id: int, data) -> bool:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                update_query = """
                    UPDATE sj_schemes SET
                        name = %s,
                        description = %s,
                        is_active = %s,
                        valid_from = %s,
                        valid_until = %s,
                        min_order_value = %s,
                        max_discount = %s,
                        discount_type = %s,
                        discount_value = %s
                    WHERE id = %s
                """
                await cursor.execute(
                    update_query,
                    (
                        data.name,
                        data.description,
                        data.isActive,
                        data.validFrom,
                        data.validUntil,
                        data.minOrderValue,
                        data.maxDiscount,
                        data.discountType,
                        data.discountValue,
                        scheme_id
                    )
                )

                if data.applicableCategories is not None:
                    await cursor.execute("DELETE FROM sj_scheme_categories WHERE scheme_id = %s", (scheme_id,))
                    cat_query = "INSERT INTO sj_scheme_categories (scheme_id, category) VALUES (%s, %s)"
                    cat_values = [(scheme_id, cat) for cat in data.applicableCategories]
                    if cat_values:
                        await cursor.executemany(cat_query, cat_values)

                if data.applicableProducts is not None:
                    await cursor.execute("DELETE FROM sj_scheme_products WHERE scheme_id = %s", (scheme_id,))
                    prod_query = "INSERT INTO sj_scheme_products (scheme_id, product_id) VALUES (%s, %s)"
                    prod_values = [(scheme_id, prod) for prod in data.applicableProducts]
                    if prod_values:
                        await cursor.executemany(prod_query, prod_values)

                if data.applicableRoles is not None:
                    await cursor.execute("DELETE FROM sj_scheme_roles WHERE scheme_id = %s", (scheme_id,))
                    role_query = "INSERT INTO sj_scheme_roles (scheme_id, role) VALUES (%s, %s)"
                    role_values = [(scheme_id, role) for role in data.applicableRoles]
                    if role_values:
                        await cursor.executemany(role_query, role_values)

                await conn.commit()
                return True

    async def delete(self, scheme_id: int) -> bool:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM sj_scheme_categories WHERE scheme_id = %s", (scheme_id,))
                await cursor.execute("DELETE FROM sj_scheme_products WHERE scheme_id = %s", (scheme_id,))
                await cursor.execute("DELETE FROM sj_scheme_roles WHERE scheme_id = %s", (scheme_id,))
                await cursor.execute("DELETE FROM sj_schemes WHERE id = %s", (scheme_id,))
                await conn.commit()
                return cursor.rowcount > 0

    async def _fetch_child_data(self, cursor, scheme_ids: List[int]) -> Dict[int, Dict[str, List[Any]]]:
        if not scheme_ids:
            return {}

        format_strings = ','.join(['%s'] * len(scheme_ids))
        
        children = {sid: {'categories': [], 'products': [], 'roles': []} for sid in scheme_ids}

        await cursor.execute(f"SELECT scheme_id, category FROM sj_scheme_categories WHERE scheme_id IN ({format_strings})", tuple(scheme_ids))
        for row in await cursor.fetchall():
            children[row['scheme_id']]['categories'].append(row['category'])

        await cursor.execute(f"SELECT scheme_id, product_id FROM sj_scheme_products WHERE scheme_id IN ({format_strings})", tuple(scheme_ids))
        for row in await cursor.fetchall():
            children[row['scheme_id']]['products'].append(row['product_id'])

        await cursor.execute(f"SELECT scheme_id, role FROM sj_scheme_roles WHERE scheme_id IN ({format_strings})", tuple(scheme_ids))
        for row in await cursor.fetchall():
            children[row['scheme_id']]['roles'].append(row['role'])

        return children

    def _map_to_response(self, row, children) -> "SchemeResponse":
        sid = row['id']
        child_data = (children[sid] if sid in children else {'categories': [], 'products': [], 'roles': []})
        return SchemeResponse(
            id=sid,
            name=row['name'],
            description=row['description'],
            isActive=bool(row['is_active']),
            validFrom=row['valid_from'],
            validUntil=row['valid_until'],
            minOrderValue=row['min_order_value'],
            maxDiscount=row['max_discount'],
            discountType=row['discount_type'],
            discountValue=row['discount_value'],
            applicableCategories=child_data['categories'],
            applicableProducts=child_data['products'],
            applicableRoles=child_data['roles'],
            createdAt=(row['created_at'] if 'created_at' in row else None),
            updatedAt=(row['updated_at'] if 'updated_at' in row else None)
        )

    async def findById(self, scheme_id: int) -> Optional["SchemeResponse"]:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM sj_schemes WHERE id = %s", (scheme_id,))
                row = await cursor.fetchone()
                if not row:
                    return None
                
                children = await self._fetch_child_data(cursor, [scheme_id])
                return self._map_to_response(row, children)

    async def findAll(self, skip: int = 0, limit: int = 100) -> List["SchemeResponse"]:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM sj_schemes LIMIT %s OFFSET %s", (limit, skip))
                rows = await cursor.fetchall()
                if not rows:
                    return []
                
                scheme_ids = [row['id'] for row in rows]
                children = await self._fetch_child_data(cursor, scheme_ids)
                
                return [self._map_to_response(row, children) for row in rows]

    async def findOne(self, filters: Dict[str, Any]) -> Optional["SchemeResponse"]:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                query = "SELECT * FROM sj_schemes"
                params = []
                if filters:
                    conditions = []
                    for k, v in filters.items():
                        if k == 'isActive':
                            conditions.append("is_active = %s")
                        elif k == 'validFrom':
                            conditions.append("valid_from = %s")
                        elif k == 'validUntil':
                            conditions.append("valid_until = %s")
                        elif k == 'minOrderValue':
                            conditions.append("min_order_value = %s")
                        elif k == 'maxDiscount':
                            conditions.append("max_discount = %s")
                        elif k == 'discountType':
                            conditions.append("discount_type = %s")
                        elif k == 'discountValue':
                            conditions.append("discount_value = %s")
                        else:
                            conditions.append(f"{k} = %s")
                        params.append(v)
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " LIMIT 1"
                await cursor.execute(query, tuple(params))
                row = await cursor.fetchone()
                if not row:
                    return None
                
                children = await self._fetch_child_data(cursor, [row['id']])
                return self._map_to_response(row, children)
