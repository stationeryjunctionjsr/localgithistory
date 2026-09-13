import json

with open("c:/Ecommerce app/.agents/explorer_survey_2/raw_calls.json", "r", encoding="utf-8") as f:
    calls = json.load(f)

order_calls = [c for c in calls if c["file"] == "orders.py" and c["caller"] not in ("router", "app")]

id_maps = {
    "users_map", "payments_map", "products_map", "_cart_products_map",
    "seller_delivery_map", "seller_docs"
}

cat_b = []
cat_a = []

for c in order_calls:
    if c["caller"] in id_maps:
        cat_b.append(c)
    else:
        cat_a.append(c)

print(f"orders.py: {len(order_calls)} total non-router calls")
print(f"  Category B (in-memory ID map lookups): {len(cat_b)}")
for c in cat_b:
    print(f"    L{c['lineno']}: [{c['caller']}] ({c['args']})")

print(f"  Category A (dict workarounds on payloads/models/internal dicts): {len(cat_a)}")

# Let's inspect unique callers in cat_a
from collections import Counter
c_counter = Counter(c["caller"] for c in cat_a)
for caller, count in c_counter.most_common():
    print(f"    {caller:35s}: {count}")
