import json
import os

with open("c:/Ecommerce app/.agents/explorer_survey_2/raw_calls.json", "r", encoding="utf-8") as f:
    calls = json.load(f)

# Define known Category B patterns:
# 1. router.get / app.get
# 2. request.headers.get / request.query_params.get / request.cookies.get
# 3. repository.get() with 0 arguments (singleton fetch: about_repository, privacy_repository)
# 4. In-memory dynamic key lookup maps:
#    - product_map / products_map / _cart_products_map
#    - users_map / sellers_map / valets_map / avail_map / order_map / seller_delivery_map / seller_docs / payments_map
#    - _guest_rec_cache / cache
#    - returned_items_qty (tally dict)
#    - min_versions (platform lookup dict)

def classify_call(c):
    caller = c["caller"]
    args = c["args"]
    file = c["file"]
    line = c["lineno"]

    # 1. Router / App GET route decorators
    if caller in ("router", "app"):
        return "Category B", "FastAPI APIRouter / App HTTP GET route decorator"

    # 2. Request headers / cookies / query params / state
    if caller in ("request.headers", "request.query_params", "request.cookies",
                  "req.headers", "req.query_params", "req.cookies", "request.state"):
        return "Category B", "HTTP Request headers/query_params/cookies lookup (Exempt standard library)"

    # 3. Repository singleton fetch (0 args)
    if caller in ("about_repository", "privacy_repository") and args == "":
        return "Category B", "Database repository singleton fetch method .get() (Exempt DB query)"

    # 4. In-memory dynamic hash maps / caches / lookup tables:
    map_callers = {
        "product_map", "products_map", "_cart_products_map",
        "users_map", "sellers_map", "valets_map", "avail_map",
        "order_map", "seller_delivery_map", "seller_docs", "payments_map",
        "_guest_rec_cache", "cache",
        "returned_items_qty", "min_versions"
    }
    if caller in map_callers:
        return "Category B", f"In-memory dynamic lookup map/cache/tally dictionary: `{caller}.get(...)`"

    # 5. Otherwise, Category A: Dictionary workaround on request payload or internal data structure / entity model
    return "Category A", f"Dictionary workaround on payload/model/entity: `{caller}.get({args})`"

classified = []
for c in calls:
    cat, reason = classify_call(c)
    classified.append({
        **c,
        "category": cat,
        "reason": reason
    })

with open("c:/Ecommerce app/.agents/explorer_survey_2/classified_calls.json", "w", encoding="utf-8") as out:
    json.dump(classified, out, indent=2)

print("Classification complete!")
