with open("backend/app/db/mysql_typed_doc_configs.py", "r", encoding="utf-8") as f:
    c = f.read()

import re

# Update customerSegments
c = re.sub(
    r'"customerSegments": _dao\(\s*"sj_customer_segments",\s*\{"type": "type", "name": "name", "description": "description", "isActive": "is_active"\},[\s\S]*?\),',
    """"customerSegments": _dao(
        "sj_customer_segments",
        {
            "type": "type", 
            "name": "name", 
            "description": "description", 
            "isActive": "is_active",
            "minAverageOrderValue": "min_avg_order_value",
            "maxAverageOrderValue": "max_avg_order_value",
            "startDate": "start_date",
            "endDate": "end_date",
            "minOrderFrequency": "min_order_freq",
            "maxOrderFrequency": "max_order_freq",
            "state": "state",
            "district": "district",
            "appUser": "app_user",
            "behavior": "behavior",
            "role": "role"
        },
        None,
        frozenset({"isActive", "appUser"})
    ),""",
    c,
)

with open("backend/app/db/mysql_typed_doc_configs.py", "w", encoding="utf-8") as f:
    f.write(c)
