import os
import re

filepath = 'backend/app/db/mysql_payment_dao.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''
            if "orderId" in query and query["orderId"]:
                if isinstance(query["orderId"], dict) and "" in query["orderId"]:
                    in_list = query["orderId"][""]
                    if not in_list:
                        where_clauses.append("1=0")
                    else:
                        id_params = {f"oid_in_{i}": oid for i, oid in enumerate(in_list)}
                        params.update(id_params)
                        id_placeholders = ", ".join([f":{k}" for k in id_params.keys()])
                        where_clauses.append(f"order_id IN ({id_placeholders})")
                else:
                    where_clauses.append("order_id = :order_id")
                    params["order_id"] = query["orderId"]
'''
content = content.replace(
'''            if "orderId" in query and query["orderId"]:
                where_clauses.append("order_id = :order_id")
                params["order_id"] = query["orderId"]''', replacement)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
