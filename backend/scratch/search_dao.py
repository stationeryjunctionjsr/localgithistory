import os
from pathlib import Path

backend_app = Path("C:/Ecommerce app/backend/app")
results = []
for p in backend_app.rglob("*.py"):
    try:
        content = p.read_text(encoding="utf-8")
        if "OracleCouponDAO" in content or "coupon_dao" in content:
            results.append(str(p))
    except Exception:
        pass

print("Files containing OracleCouponDAO or coupon_dao:")
for r in results:
    print(" ", r)
