import json
import sys

files = [
    "tests/test_analytics_and_tracking.py",
    "tests/test_bxgy_deal_rules.py",
    "tests/test_catalog_routers_pydantic.py",
    "tests/test_concurrency_e2e.py",
    "tests/test_core_endpoints.py",
    "tests/test_coupon_mode.py",
    "tests/test_delivery_zones_and_checkout.py",
    "tests/test_e2e.py",
    "tests/test_flow3.py",
    "tests/test_full_integrated_e2e.py",
    "tests/test_health.py",
    "tests/test_multiseller_coupon_payout.py",
    "tests/test_multiseller_e2e.py",
    "tests/test_new_features.py",
    "tests/test_notifications_optimization.py",
    "tests/test_orders_optimization.py",
    "tests/test_overall_optimization.py",
    "tests/test_payouts_e2e.py",
    "tests/test_products_filtering.py",
    "tests/test_recommendations.py",
    "tests/test_referrals.py",
    "tests/test_returns_e2e.py",
    "tests/test_reviews_notifications.py",
    "tests/test_router_pydantic_refactor.py",
    "tests/test_shipping_discount_logic.py",
    "tests/test_wholesaler_dues.py",
    "tests/test_bundle_recommendations.py"
]

prompt_template = \"\"\"
You need to fix the file {file}.
The backend repository layer has been fully migrated to pure Pydantic. It now takes Pydantic models (like OrderInternalCreate, NotificationInternalCreate) and returns Pydantic models.
Your task for this file:
1. Import the necessary Pydantic models from pp.models.daos or pp.models.daos_flat or pp.models.schemas. If you are unsure, just import from both or try to find it. Or just use:
`python
try:
    from app.models.daos import ModelName
except ImportError:
    from app.models.daos_flat import ModelName
`
2. Wrap dictionary payloads in the models when calling epository.create(...) or epository.update(...). Note: For _id, inject "_id": __import__("uuid").uuid4().hex if the test doesn't provide one and the model requires it (like NotificationInternalCreate).
3. Change dictionary access obj["camelCase"] to attribute access obj.snake_case when interacting with repository returns (e.g. order, 
otification, coupon). **DO NOT** change es.json()["camelCase"] as those are HTTP responses.
4. For DeliverySlotConfigCreate, use zoneIds instead of zone_ids.
5. If you see epository.findAll(dict), pass the dict as **dict to the corresponding Filter model, e.g. NotificationFilter(**dict).

Use eplace_file_content or un_command (with sed/python) to modify the file. Output the final fixed code or use tools to fix it. Once you finish modifying the file and you are confident it is correct, send a message back with 'DONE: {file}'.
\"\"\"

print(len(files))
