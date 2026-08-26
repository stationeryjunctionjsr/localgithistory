import re
from typing import Dict

content = open("app/db/mysql_tracking_dao.py", "r", encoding="utf-8").read()

replacement = """    "cartValue": "cart_value",
    "cartItems": "cart_items",
    "isReturning": "is_returning",
    "source": "source",
    "campaign": "campaign",
    "os": "os","""
content = content.replace('    "cartValue": "cart_value",\n    "os": "os",', replacement)

delete_many_code = """
    async def deleteMany(self, query: Dict) -> int:
        from sqlalchemy import text
        factory = self._factory()
        where_clauses = []
        params = {}
        for k, v in query.items():
            if k in _TRACKING_SCALAR:
                where_clauses.append(f"{_TRACKING_SCALAR[k]} = :{k}")
                params[k] = v
            elif k in ("_id", "id"):
                where_clauses.append("id = :id")
                params["id"] = int(v) if str(v).isdigit() else 0
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        async with factory() as session:
            res = await session.execute(text(f"DELETE FROM {self.TABLE} WHERE {where_sql}"), params)
            await session.commit()
            return res.rowcount
"""
if "def deleteMany" not in content:
    content += delete_many_code

content = re.sub(r'for k, v in data\.get\("payload", \{\}\)\.items\(\):.*?v\}\)\)', "pass", content, flags=re.DOTALL)
content = re.sub(r"pl_res = await session\.execute.*?r\.payload_value", "", content, flags=re.DOTALL)
content = re.sub(r'if "payload" not in data:.*?data\["payload"\]\[k\] = v', "", content, flags=re.DOTALL)
content = re.sub(r'if "payload" not in merged:.*?merged\["payload"\]\[k\] = v', "", content, flags=re.DOTALL)
content = re.sub(r'out\["payload"\] = payload', 'out["payload"] = {}', content)

with open("app/db/mysql_tracking_dao.py", "w", encoding="utf-8") as f:
    f.write(content)
