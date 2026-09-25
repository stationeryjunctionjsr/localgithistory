import os
import re

filepath = 'app/db/mysql_brand_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove __map_to_schema
text = re.sub(r'\s*def __map_to_schema\(self, r\) -> BrandResponse:.*?(?=\s*async def findAll)', '', text, flags=re.DOTALL)

# 2. Update findAll
find_all_new = '''
    async def findAll(self, query: Optional[Dict] = None) -> List[BrandResponse]:
        factory = self._factory()
        if not factory:
            return []
            
        where_clauses = []
        params = {}
        if query:
            for k, v in query.items():
                if k in ("_id", "id"):
                    where_clauses.append("id = :id")
                    params["id"] = int(v) if str(v).isdigit() else None
                elif k == "slug":
                    where_clauses.append("slug = :slug")
                    params["slug"] = v
                elif k == "is_active":
                    where_clauses.append("is_active = :is_active")
                    params["is_active"] = 1 if v else 0
                elif k == "name":
                    where_clauses.append("name = :name")
                    params["name"] = v
                elif k == "show_in_mobile_homepage":
                    where_clauses.append("show_in_mobile_homepage = :show_in_mobile_homepage")
                    params["show_in_mobile_homepage"] = 1 if v else 0
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id AS _id, external_id, name, slug, image_url AS logo_url, show_in_mobile_homepage, is_active, created_at, updated_at
                    FROM {self.TABLE}
                    WHERE {where_sql}
                    """
                ),
                params
            )
            rows = result.fetchall()
            
        return [BrandResponse.model_validate(r._mapping) for r in rows]
'''
text = re.sub(r'\s*async def findAll\(self, query: Optional\[Dict\] = None\) -> List\[BrandResponse\]:.*?(?=\s*async def findOne)', find_all_new, text, flags=re.DOTALL)

# 3. Update findById
find_by_id_new = '''
    async def findById(self, id: str) -> Optional[BrandResponse]:
        factory = self._factory()
        if not factory:
            return None
        bid = int(id) if str(id).isdigit() else None
        async with factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT id AS _id, external_id, name, slug, image_url AS logo_url, show_in_mobile_homepage, is_active, created_at, updated_at
                    FROM {self.TABLE} WHERE id = :id
                    """
                ),
                {"id": bid},
            )
            row = result.fetchone()
        return BrandResponse.model_validate(row._mapping) if row else None
'''
text = re.sub(r'\s*async def findById\(self, id: str\) -> Optional\[BrandResponse\]:.*?(?=\s*async def create)', find_by_id_new, text, flags=re.DOTALL)

# 4. Remove 'from app.models.brand import Brand'
text = text.replace('from app.models.brand import Brand\n', '')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
