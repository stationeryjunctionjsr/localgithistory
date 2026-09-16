import os
import re
filepath = 'backend/app/db/mysql_coupons_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace findAll
old_findall = '''    async def findAll(self) -> List[CouponResponse]:
        async with self._factory()() as session:
            query = text("SELECT * FROM sj_coupons")
            result = await session.execute(query)
            rows = result.fetchall()
            responses = []
            for row in rows:
                responses.append(await self._map_to_response(row))
            return responses'''

new_findall = '''    async def findAll(self, query: Optional[Dict[str, Any]] = None) -> List[CouponResponse]:
        query = query or {}
        async with self._factory()() as session:
            sql = "SELECT * FROM sj_coupons"
            params = {}
            if query:
                conditions = []
                for k, v in query.items():
                    if k == "isActive":
                        conditions.append("is_active = :isActive")
                        params["isActive"] = int(v) if isinstance(v, bool) else v
                    elif k == "method":
                        conditions.append("method = :method")
                        params["method"] = v
                    elif k == "typeOfDiscount":
                        conditions.append("type_of_discount = :typeOfDiscount")
                        params["typeOfDiscount"] = v
                    elif k == "id":
                        conditions.append("id = :id")
                        params["id"] = v
                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)
            
            q = text(sql)
            result = await session.execute(q, params)
            rows = result.fetchall()
            responses = []
            for row in rows:
                responses.append(await self._map_to_response(row))
            return responses'''

if old_findall in content:
    content = content.replace(old_findall, new_findall)
    # also add typing
    if 'from typing import ' in content and 'Dict' not in content:
        content = content.replace('from typing import ', 'from typing import Dict, Any, ')
    elif 'Dict' not in content:
        content = 'from typing import Dict, Any\n' + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched findAll")
else:
    print("Could not find old findAll")
