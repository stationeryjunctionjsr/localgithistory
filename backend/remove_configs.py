import re

with open("backend/app/db/mysql_typed_doc_configs.py", "r", encoding="utf-8") as f:
    c = f.read()

# Replace all the DAOs that we moved to generated DAOs
# The keys of TABLES_CONFIG in generate_daos.py:
keys_to_remove = [
    "activities",
    "notifications",
    "returnRequests",
    "schemes",
    "contacts",
    "supportTickets",
    "deviceSubscriptions",
    "collections",
    "searchTags",
    "deliveryCharges",
    "deliveryChargeDefaults",
    "deliverySlots",
    "deliveryZones",
    "events",
]

for k in keys_to_remove:
    # regex to match "key": _dao( ... ),
    pattern = r'"' + k + r'": _dao\([^)]+\),'
    c = re.sub(pattern, "", c, flags=re.DOTALL)

with open("backend/app/db/mysql_typed_doc_configs.py", "w", encoding="utf-8") as f:
    f.write(c)
