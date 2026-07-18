import os
from pathlib import Path

backend_app = Path("C:/Ecommerce app/backend/app")
results = []
for p in backend_app.rglob("*.py"):
    try:
        content = p.read_text(encoding="utf-8")
        if "sj_coupons" in content.lower() or "from coupons" in content.lower():
            results.append(str(p))
    except Exception:
        pass

print("Files containing sj_coupons or coupons raw SQL:")
for r in results:
    print(" ", r)
